package sphinxjava;

import com.sun.source.doctree.*;
import com.sun.source.util.DocTreePath;
import com.sun.source.util.DocTrees;
import java.nio.file.*;
import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import javax.lang.model.type.*;
import javax.lang.model.util.Elements;
import javax.lang.model.util.Types;
import javax.tools.Diagnostic;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import jdk.javadoc.doclet.*;

/** Extracts source declarations and semantic documentation using public JDK APIs. */
public final class SphinxDoclet implements Doclet {
  private static final String THROWS = "throws:";
  // shortcut: conservatively detect markup comments; replace with a markup parser when
  // supporting regions/actions.
  private static final Pattern SNIPPET_MARKUP =
      Pattern.compile("(?s).*(?://|#)[^\\r\\n]*@(?:start|end|highlight|replace|link)\\b.*");

  private Reporter reporter;
  private DocTrees trees;
  private Elements elements;
  private Types types;
  private Path output;
  private final Set<String> warnings = new TreeSet<>();
  private final Map<Element, Map<String, Part>> comments = new HashMap<>();

  /** Documentation content together with the declaration whose comment supplied it. */
  private record Part(Element owner, String label, List<? extends DocTree> trees) {}

  /** Fluent builder for the model's DOM elements. */
  private record Xml(org.w3c.dom.Element node) {
    Xml add(String tag) {
      var child = node.getOwnerDocument().createElement(tag);
      node.appendChild(child);
      return new Xml(child);
    }

    Xml set(String name, String value) {
      node.setAttribute(name, value);
      return this;
    }

    void addText(String tag, String value) {
      var child = add(tag).node;
      child.appendChild(child.getOwnerDocument().createTextNode(value));
    }

    void addAttr(String name, String value) {
      add("attr").set("name", name).node.setTextContent(value);
    }
  }

  @Override
  public void init(Locale locale, Reporter reporter) {
    this.reporter = reporter;
  }

  @Override
  public String getName() {
    return "SphinxDoclet";
  }

  @Override
  public SourceVersion getSupportedSourceVersion() {
    return SourceVersion.latestSupported();
  }

  @Override
  public Set<? extends Option> getSupportedOptions() {
    return Set.of(
        new Option() {
          @Override
          public int getArgumentCount() {
            return 1;
          }

          @Override
          public String getDescription() {
            return "Write versioned Sphinx API XML";
          }

          @Override
          public Kind getKind() {
            return Kind.STANDARD;
          }

          @Override
          public List<String> getNames() {
            return List.of("--sphinx-output");
          }

          @Override
          public String getParameters() {
            return "file";
          }

          @Override
          public boolean process(String name, List<String> arguments) {
            output = Path.of(arguments.getFirst());
            return true;
          }
        });
  }

  @Override
  public boolean run(DocletEnvironment env) {
    trees = env.getDocTrees();
    elements = env.getElementUtils();
    types = env.getTypeUtils();
    if (output == null) {
      reporter.print(Diagnostic.Kind.ERROR, "--sphinx-output is required");
      return false;
    }
    try {
      var document = DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument();
      var root = new Xml(document.createElement("api"));
      document.appendChild(root.node());
      root.set("schema", "1").set("extractor", "0.1.0");
      var included =
          env.getIncludedElements().stream()
              .filter(e -> e instanceof TypeElement && visible(e, false) && !hidden(e))
              .map(TypeElement.class::cast)
              .sorted(Comparator.comparing(t -> t.getQualifiedName().toString()))
              .toList();
      var packages = new TreeMap<String, PackageElement>();
      for (var type : included) {
        var pkg = elements.getPackageOf(type);
        packages.put(pkg.toString(), pkg);
      }
      for (var pkg : packages.values()) {
        documentation(root.add("package").set("name", pkg.getQualifiedName().toString()), pkg);
      }
      for (var type : included) {
        var node = declaration(root, "type", type);
        type.getEnclosedElements().stream()
            .filter(e -> e instanceof ExecutableElement || e instanceof VariableElement)
            .filter(e -> visible(e, false) && !hidden(e))
            .sorted(Comparator.comparing(this::id))
            .forEach(member -> declaration(node, "member", member));
      }
      warnings.forEach(warning -> root.addText("diagnostic", warning));
      var transformer = TransformerFactory.newInstance().newTransformer();
      transformer.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
      transformer.setOutputProperty(OutputKeys.INDENT, "yes");
      transformer.transform(new DOMSource(document), new StreamResult(output.toFile()));
      return true;
    } catch (Exception e) {
      reporter.print(Diagnostic.Kind.ERROR, "Sphinx extraction failed: " + e);
      return false;
    }
  }

  /** Whether the declaration and all enclosing declarations are public (or protected). */
  private static boolean visible(Element e, boolean publicOnly) {
    while (e instanceof TypeElement
        || e instanceof ExecutableElement
        || e instanceof VariableElement) {
      var modifiers = e.getModifiers();
      boolean exported =
          modifiers.contains(Modifier.PUBLIC)
              || (!publicOnly && modifiers.contains(Modifier.PROTECTED));
      if (!exported) {
        return false;
      }
      e = e.getEnclosingElement();
    }
    return true;
  }

  private boolean hidden(Element e) {
    var comment = trees.getDocCommentTree(e);
    return comment != null
        && comment.getBlockTags().stream().anyMatch(t -> t.getKind() == DocTree.Kind.HIDDEN);
  }

  /** Records a diagnostic; {@code template} is a {@link String#format} pattern. */
  private void warn(Element owner, String template, Object... args) {
    warnings.add(id(owner) + ": " + (args.length == 0 ? template : template.formatted(args)));
  }

  private static String join(Collection<?> values) {
    return values.stream().map(Object::toString).collect(Collectors.joining(", "));
  }

  // Declarations and signatures

  private String id(Element e) {
    if (e instanceof QualifiedNameable named) {
      return named.getQualifiedName().toString();
    }
    String id = id(e.getEnclosingElement()) + "#" + e.getSimpleName();
    if (e instanceof ExecutableElement method) {
      id +=
          method.getParameters().stream()
              .map(p -> linkType(types.erasure(p.asType())))
              .collect(Collectors.joining(",", "(", ")"));
    }
    return id;
  }

  private static String linkType(TypeMirror type) {
    return switch (type) {
      case ArrayType array -> linkType(array.getComponentType()) + "[]";
      case TypeVariable variable -> variable.asElement().getSimpleName().toString();
      case DeclaredType declared ->
          ((TypeElement) declared.asElement()).getQualifiedName().toString();
      default ->
          type.getKind().isPrimitive()
              ? type.getKind().name().toLowerCase(Locale.ROOT)
              : type.toString();
    };
  }

  private static String typeParameters(List<? extends TypeParameterElement> parameters) {
    if (parameters.isEmpty()) {
      return "";
    }
    return parameters.stream()
        .map(SphinxDoclet::typeParameter)
        .collect(Collectors.joining(", ", "<", ">"));
  }

  private static String typeParameter(TypeParameterElement parameter) {
    var bounds = parameter.getBounds();
    if (bounds.size() == 1 && bounds.getFirst().toString().equals("java.lang.Object")) {
      return parameter.getSimpleName().toString();
    }
    return parameter.getSimpleName()
        + " extends "
        + bounds.stream().map(Object::toString).collect(Collectors.joining(" & "));
  }

  private static String annotations(Element e) {
    return e.getAnnotationMirrors().stream().map(a -> a + " ").collect(Collectors.joining());
  }

  private String signature(Element e) {
    String modifiers = e.getModifiers().stream().map(m -> m + " ").collect(Collectors.joining());
    String prefix = annotations(e) + modifiers;
    return switch (e) {
      case TypeElement type -> prefix + typeSignature(type);
      case ExecutableElement method -> prefix + methodSignature(method);
      case VariableElement variable -> prefix + variableSignature(variable);
      default -> throw new IllegalArgumentException("Unexpected declaration " + e);
    };
  }

  private static String typeSignature(TypeElement type) {
    var kind = type.getKind();
    var s = new StringBuilder();
    s.append(
        kind == ElementKind.ANNOTATION_TYPE ? "@interface" : kind.name().toLowerCase(Locale.ROOT));
    s.append(' ').append(type.getQualifiedName()).append(typeParameters(type.getTypeParameters()));
    if (kind == ElementKind.RECORD) {
      s.append(
          type.getRecordComponents().stream()
              .map(c -> annotations(c) + c.asType() + " " + c.getSimpleName())
              .collect(Collectors.joining(", ", "(", ")")));
    }
    var superclass = type.getSuperclass();
    if (kind == ElementKind.CLASS
        && superclass.getKind() != TypeKind.NONE
        && !superclass.toString().equals("java.lang.Object")) {
      s.append(" extends ").append(superclass);
    }
    if (!type.getInterfaces().isEmpty()) {
      s.append(kind.isInterface() ? " extends " : " implements ");
      s.append(join(type.getInterfaces()));
    }
    if (!type.getPermittedSubclasses().isEmpty()) {
      s.append(" permits ").append(join(type.getPermittedSubclasses()));
    }
    return s.toString();
  }

  private static String methodSignature(ExecutableElement method) {
    var s = new StringBuilder();
    if (!method.getTypeParameters().isEmpty()) {
      s.append(typeParameters(method.getTypeParameters())).append(' ');
    }
    if (method.getKind() == ElementKind.CONSTRUCTOR) {
      s.append(method.getEnclosingElement().getSimpleName());
    } else {
      s.append(method.getReturnType()).append(' ').append(method.getSimpleName());
    }
    var parameters = method.getParameters();
    var rendered = new ArrayList<String>();
    for (int i = 0; i < parameters.size(); i++) {
      var parameter = parameters.get(i);
      String type = parameter.asType().toString();
      if (method.isVarArgs() && i == parameters.size() - 1) {
        type = type.substring(0, type.length() - 2) + "...";
      }
      rendered.add(annotations(parameter) + type + " " + parameter.getSimpleName());
    }
    s.append('(').append(String.join(", ", rendered)).append(')');
    if (!method.getThrownTypes().isEmpty()) {
      s.append(" throws ").append(join(method.getThrownTypes()));
    }
    if (method.getDefaultValue() != null) {
      s.append(" default ").append(method.getDefaultValue());
    }
    return s.toString();
  }

  private String variableSignature(VariableElement variable) {
    var value = variable.getConstantValue();
    String constant = value == null ? "" : " = " + elements.getConstantExpression(value);
    return variable.asType() + " " + variable.getSimpleName() + constant;
  }

  private Xml declaration(Xml parent, String tag, Element e) {
    var node =
        parent
            .add(tag)
            .set("id", id(e))
            .set("name", e.getSimpleName().toString())
            .set("kind", e.getKind().name().toLowerCase(Locale.ROOT))
            .set("visibility", visible(e, true) ? "public" : "protected")
            .set("package", elements.getPackageOf(e).getQualifiedName().toString())
            .set("signature", signature(e));
    documentation(node, e);
    return node;
  }

  // Comment parts and inheritance

  /** Returns the declaration's own comment parts, keyed by kind and parameter position. */
  private Map<String, Part> parts(Element e) {
    var cached = comments.get(e);
    if (cached != null) {
      return cached;
    }
    var result = new LinkedHashMap<String, Part>();
    comments.put(e, result);
    var comment = trees.getDocCommentTree(e);
    if (comment == null) {
      return result;
    }
    if (elements.getDocCommentKind(e) == Elements.DocCommentKind.END_OF_LINE) {
      warn(
          e,
          "Markdown documentation comments are not supported; use traditional /** comments for"
              + " this release.");
    }
    if (!comment.getFullBody().isEmpty()) {
      result.put("body", new Part(e, "", comment.getFullBody()));
    }
    int see = 0;
    for (var tag : comment.getBlockTags()) {
      switch (tag) {
        case ParamTree param -> putParam(result, e, param);
        case ReturnTree ret -> result.put("return", new Part(e, "", ret.getDescription()));
        case ThrowsTree thrown -> putThrows(result, e, thrown);
        case SeeTree s -> result.put("see:" + see++, new Part(e, "", s.getReference()));
        case SinceTree since -> result.put("since", new Part(e, "", since.getBody()));
        case DeprecatedTree d -> result.put("deprecated", new Part(e, "", d.getBody()));
        default -> {
          if (tag.getKind() != DocTree.Kind.HIDDEN) {
            warn(e, "Unsupported block tag %s; retain it in handwritten guides.", tag.getKind());
          }
        }
      }
    }
    return result;
  }

  private void putParam(Map<String, Part> result, Element e, ParamTree param) {
    String name = param.getName().toString();
    String key = "param:" + name;
    if (e instanceof ExecutableElement method) {
      var declared = param.isTypeParameter() ? method.getTypeParameters() : method.getParameters();
      int index = -1;
      for (int i = 0; i < declared.size(); i++) {
        if (declared.get(i).getSimpleName().contentEquals(name)) {
          index = i;
        }
      }
      if (index < 0) {
        warn(e, "@param %s does not name a declared parameter.", name);
      }
      key = (param.isTypeParameter() ? "typeparam:" : "param:") + index;
    }
    String label = param.isTypeParameter() ? "<" + name + ">" : name;
    result.put(key, new Part(e, label, param.getDescription()));
  }

  private void putThrows(Map<String, Part> result, Element e, ThrowsTree thrown) {
    var target = resolve(e, thrown.getExceptionName());
    String name = target == null ? thrown.getExceptionName().toString() : id(target);
    // Inheritance must copy every description of the same exception.
    result.merge(
        THROWS + name,
        new Part(e, name, thrown.getDescription()),
        (first, next) -> {
          var paragraph =
              trees
                  .getDocTreeFactory()
                  .newStartElementTree(elements.getName("p"), List.of(), false);
          var content = new ArrayList<DocTree>(first.trees());
          content.add(paragraph);
          content.addAll(next.trees());
          return new Part(e, name, content);
        });
  }

  private ExecutableElement overridden(ExecutableElement method) {
    var owner = (TypeElement) method.getEnclosingElement();
    var result = search(method, owner, owner, new HashSet<>());
    if (result != null) {
      return result;
    }
    return search(method, owner, elements.getTypeElement("java.lang.Object"), new HashSet<>());
  }

  private ExecutableElement search(
      ExecutableElement method, TypeElement owner, TypeElement current, Set<TypeElement> seen) {
    if (!seen.add(current)) {
      return null;
    }
    for (var e : current.getEnclosedElements()) {
      if (e instanceof ExecutableElement candidate
          && candidate.getKind() == ElementKind.METHOD
          && elements.overrides(method, candidate, owner)) {
        return candidate;
      }
    }
    if (types.asElement(current.getSuperclass()) instanceof TypeElement superclass
        && !superclass.getQualifiedName().contentEquals("java.lang.Object")) {
      var found = search(method, owner, superclass, seen);
      if (found != null) {
        return found;
      }
    }
    for (var type : current.getInterfaces()) {
      var found = search(method, owner, (TypeElement) types.asElement(type), seen);
      if (found != null) {
        return found;
      }
    }
    return null;
  }

  /** Maps a child's throws key to the ancestor's key, following generic substitution. */
  private String inheritedKey(ExecutableElement child, ExecutableElement ancestor, String key) {
    if (!key.startsWith(THROWS)) {
      return key;
    }
    TypeMirror requested = null;
    for (var type : child.getThrownTypes()) {
      if (key.equals(THROWS + id(types.asElement(type)))) {
        requested = type;
      }
    }
    if (requested == null
        && elements.getTypeElement(key.substring(THROWS.length())) instanceof TypeElement type) {
      requested = type.asType();
    }
    if (requested == null) {
      return key;
    }
    var owner = (DeclaredType) child.getEnclosingElement().asType();
    var member = (ExecutableType) types.asMemberOf(owner, ancestor);
    String subtypeMatch = key;
    for (int i = 0; i < ancestor.getThrownTypes().size(); i++) {
      if (!(ancestor.getThrownTypes().get(i) instanceof TypeVariable declared)) {
        continue;
      }
      var substituted = member.getThrownTypes().get(i);
      if (declared.asElement().getEnclosingElement().equals(ancestor)
          && child.getTypeParameters().size() == ancestor.getTypeParameters().size()) {
        int position = ancestor.getTypeParameters().indexOf(declared.asElement());
        substituted = child.getTypeParameters().get(position).asType();
      }
      String candidate = THROWS + id(types.asElement(declared));
      if (types.isSameType(requested, substituted)) {
        return candidate;
      }
      if (subtypeMatch.equals(key) && types.isSubtype(requested, substituted)) {
        subtypeMatch = candidate;
      }
    }
    return subtypeMatch;
  }

  private Part findPart(Element e, String key, Set<Element> seen) {
    if (!seen.add(e)) {
      return null;
    }
    Part part = parts(e).get(key);
    if (part != null && !part.trees().isEmpty()) {
      return part;
    }
    if (key.startsWith(THROWS)) {
      var requested = elements.getTypeElement(key.substring(THROWS.length()));
      for (var entry : parts(e).entrySet()) {
        if (!entry.getKey().startsWith(THROWS)) {
          continue;
        }
        var documented = elements.getTypeElement(entry.getKey().substring(THROWS.length()));
        if (requested != null
            && documented != null
            && types.isSubtype(requested.asType(), documented.asType())) {
          return entry.getValue();
        }
      }
    }
    if (e instanceof ExecutableElement method && e.getKind() == ElementKind.METHOD) {
      var parent = overridden(method);
      if (parent != null) {
        return findPart(parent, inheritedKey(method, parent, key), seen);
      }
    }
    return null;
  }

  /** Returns the method if it is declared in source and overrides an ancestor, else null. */
  private ExecutableElement overridingMethod(Element e) {
    if (e instanceof ExecutableElement method
        && method.getKind() == ElementKind.METHOD
        && trees.getTree(e) != null
        && overridden(method) != null) {
      return method;
    }
    return null;
  }

  private void documentation(Xml node, Element e) {
    var doc = node.add("doc");
    var own = parts(e);
    var keys = new LinkedHashSet<>(own.keySet());
    keys.add("body");
    var method = overridingMethod(e);
    if (method != null) {
      for (int i = 0; i < method.getParameters().size(); i++) {
        keys.add("param:" + i);
      }
      for (int i = 0; i < method.getTypeParameters().size(); i++) {
        keys.add("typeparam:" + i);
      }
      if (method.getReturnType().getKind() != TypeKind.VOID) {
        keys.add("return");
      }
      for (var type : method.getThrownTypes()) {
        keys.add(THROWS + id(types.asElement(type)));
      }
    }
    for (var key : keys) {
      Part part = own.get(key);
      if (part == null && method != null) {
        part = findPart(e, key, new HashSet<>());
      }
      if (part == null) {
        if (method != null) {
          warn(
              e,
              "Cannot inherit %s; provide the overridden method's source documentation or"
                  + " document this part explicitly.",
              key);
        }
        continue;
      }
      var xml = doc.add("part").set("kind", key.split(":", 2)[0]).set("label", label(e, key, part));
      String context = key.startsWith(THROWS) ? THROWS + part.label() : key;
      emit(xml, part.owner(), context, part.trees(), new HashSet<>());
    }
  }

  /** Labels follow the documented declaration, even when the prose is inherited. */
  private static String label(Element e, String key, Part part) {
    if (key.startsWith(THROWS)) {
      return key.substring(THROWS.length()).replaceFirst(".*#", "");
    }
    boolean typeParameter = key.startsWith("typeparam:");
    if (!(e instanceof ExecutableElement method) || !(typeParameter || key.startsWith("param:"))) {
      return part.label();
    }
    int index = Integer.parseInt(key.split(":")[1]);
    var declared = typeParameter ? method.getTypeParameters() : method.getParameters();
    String name =
        index >= 0 && index < declared.size()
            ? declared.get(index).getSimpleName().toString()
            : part.label();
    return typeParameter ? "<" + name + ">" : name;
  }

  // Comment content

  private Element resolve(Element owner, DocTree reference) {
    var comment = trees.getDocCommentTree(owner);
    var path = trees.getPath(owner);
    if (comment == null || path == null) {
      return null;
    }
    var docPath = DocTreePath.getPath(new DocTreePath(path, comment), reference);
    return docPath == null ? null : trees.getElement(docPath);
  }

  private void emit(
      Xml parent, Element owner, String key, List<? extends DocTree> content, Set<String> chain) {
    for (var tree : content) {
      switch (tree) {
        // ErroneousTree extends TextTree, so it must come first.
        case ErroneousTree error -> {
          warn(owner, "Malformed Javadoc: %s", error.getDiagnostic().getMessage(Locale.ROOT));
          parent.addText("literal", error.getBody());
        }
        case TextTree text -> parent.addText("text", text.getBody());
        case LiteralTree literal -> {
          String tag = tree.getKind() == DocTree.Kind.CODE ? "code" : "literal";
          parent.addText(tag, literal.getBody().getBody());
        }
        case SnippetTree snippet -> snippet(parent, owner, snippet);
        case EntityTree entity -> parent.addText("text", characters(entity));
        case LinkTree link -> {
          boolean plain = tree.getKind() == DocTree.Kind.LINK_PLAIN;
          reference(parent, owner, link.getReference(), link.getLabel(), plain);
        }
        case ReferenceTree ref -> reference(parent, owner, ref, List.of(), false);
        case StartElementTree start -> startElement(parent, start);
        case EndElementTree end -> parent.add("end").set("name", end.getName().toString());
        case InheritDocTree inherit -> inheritDoc(parent, owner, key, inherit, chain);
        case ReturnTree ret -> emit(parent, owner, "return", ret.getDescription(), chain);
        default -> {
          if (tree.getKind() != DocTree.Kind.COMMENT) {
            warn(
                owner,
                "Unsupported Javadoc construct %s; use traditional text or <pre>{@code ...}</pre>"
                    + " (Markdown expansion is deferred).",
                tree.getKind());
            parent.addText("literal", tree.toString());
          }
        }
      }
    }
  }

  private String characters(EntityTree entity) {
    return Objects.requireNonNullElse(trees.getCharacters(entity), entity.toString());
  }

  private void startElement(Xml parent, StartElementTree start) {
    var node =
        parent
            .add("start")
            .set("name", start.getName().toString())
            .set("closed", Boolean.toString(start.isSelfClosing()));
    for (var attribute : start.getAttributes()) {
      if (attribute instanceof AttributeTree a) {
        String value =
            a.getValue().stream()
                .map(v -> v instanceof EntityTree entity ? characters(entity) : v.toString())
                .collect(Collectors.joining());
        node.addAttr(a.getName().toString(), value);
      }
    }
  }

  private void reference(
      Xml parent, Element owner, ReferenceTree ref, List<? extends DocTree> label, boolean plain) {
    if (ref == null) {
      warn(owner, "Malformed Javadoc: link is missing a reference target.");
      parent.addText("literal", "[missing link target]");
      return;
    }
    var link = parent.add("link").set("plain", Boolean.toString(plain));
    var target = resolve(owner, ref);
    link.set("target", target == null ? ref.toString() : id(target));
    if (target == null) {
      warn(
          owner,
          "Unresolved Javadoc reference %s; check spelling, source paths and classpath.",
          ref);
    } else {
      String role =
          switch (target) {
            case TypeElement _ -> "type";
            case ExecutableElement _ -> "method";
            case PackageElement _ -> "package";
            default -> "field";
          };
      link.set("role", role);
      javadocLocation(link, target);
    }
    if (label.isEmpty()) {
      link.addText("text", ref.toString());
    } else {
      emit(link, owner, "label", label, new HashSet<>());
    }
  }

  /** Records where standard Javadoc publishes the target, for external Javadoc links. */
  private void javadocLocation(Xml link, Element target) {
    Element type = target;
    while (type != null && !(type instanceof TypeElement) && !(type instanceof PackageElement)) {
      type = type.getEnclosingElement();
    }
    if (type == null) {
      return;
    }
    String pkg = elements.getPackageOf(type).getQualifiedName().toString();
    String path = pkg.isEmpty() ? "" : pkg.replace('.', '/') + "/";
    if (type instanceof TypeElement t) {
      String name = t.getQualifiedName().toString();
      path += name.substring(pkg.isEmpty() ? 0 : pkg.length() + 1) + ".html";
    } else {
      path += "package-summary.html";
    }
    var module = elements.getModuleOf(type);
    String moduleName =
        module == null || module.isUnnamed() ? "" : module.getQualifiedName().toString();
    String fragment =
        switch (target) {
          case ExecutableElement method -> methodFragment(method);
          case VariableElement variable -> variable.getSimpleName().toString();
          default -> "";
        };
    link.set("path", path).set("module", moduleName).set("fragment", fragment);
  }

  private static String methodFragment(ExecutableElement method) {
    String fragment =
        method.getSimpleName()
            + method.getParameters().stream()
                .map(p -> linkType(p.asType()))
                .collect(Collectors.joining(",", "(", ")"));
    return method.isVarArgs() ? fragment.substring(0, fragment.length() - 3) + "...)" : fragment;
  }

  private void snippet(Xml parent, Element owner, SnippetTree snippet) {
    String language = "java";
    boolean supported = snippet.getBody() != null && snippet.getAttributes().size() <= 1;
    for (var attribute : snippet.getAttributes()) {
      if (attribute instanceof AttributeTree a && a.getName().contentEquals("lang")) {
        language = a.getValue().stream().map(Object::toString).collect(Collectors.joining());
        supported &= language.matches("[A-Za-z0-9_+.-]+");
      } else {
        supported = false;
      }
    }
    String body = snippet.getBody() == null ? "" : snippet.getBody().getBody();
    supported &= !SNIPPET_MARKUP.matcher(body).matches();
    if (!supported) {
      warn(
          owner,
          "Unsupported snippet attributes or markup; use an inline body with optional lang,"
              + " without files, regions, IDs or markup actions.");
      parent.addText("literal", snippet.toString());
      return;
    }
    parent.add("start").set("name", "pre").addAttr("lang", language);
    parent.addText("literal", body.stripIndent());
    parent.add("end").set("name", "pre");
  }

  private void inheritDoc(
      Xml parent, Element owner, String key, InheritDocTree inherit, Set<String> chain) {
    boolean inheritable =
        key.equals("body")
            || key.equals("return")
            || key.startsWith("param:")
            || key.startsWith("typeparam:")
            || key.startsWith(THROWS);
    if (!(owner instanceof ExecutableElement method)
        || method.getKind() != ElementKind.METHOD
        || !inheritable) {
      warn(
          owner,
          "inheritDoc is only valid in overriding method descriptions, parameters, returns and"
              + " throws.");
      parent.addText("literal", "[unresolved inheritDoc]");
      return;
    }
    ExecutableElement ancestor = overridden(method);
    if (inherit.getSupertype() != null) {
      var owningType = (TypeElement) method.getEnclosingElement();
      ancestor =
          resolve(owner, inherit.getSupertype()) instanceof TypeElement supertype
              ? search(method, owningType, supertype, new HashSet<>())
              : null;
    }
    String step = id(owner) + ":" + key;
    Part inherited =
        ancestor == null
            ? null
            : findPart(ancestor, inheritedKey(method, ancestor, key), new HashSet<>());
    if (inherited == null || !chain.add(step)) {
      warn(
          owner,
          "Cannot resolve inheritDoc for %s; provide ancestor source documentation or write this"
              + " part explicitly.",
          key);
      parent.addText("literal", "[unresolved inheritDoc]");
      return;
    }
    String context = key.startsWith(THROWS) ? THROWS + inherited.label() : key;
    emit(parent, inherited.owner(), context, inherited.trees(), chain);
    chain.remove(step);
  }
}
