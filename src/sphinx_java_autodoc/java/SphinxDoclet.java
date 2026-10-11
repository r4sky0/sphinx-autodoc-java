package sphinxjava;

import com.sun.source.doctree.*;
import com.sun.source.util.DocTreePath;
import com.sun.source.util.DocTrees;
import java.nio.file.*;
import java.util.*;
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
import org.w3c.dom.Document;

/** Extracts source declarations and semantic documentation using public JDK APIs. */
public final class SphinxDoclet implements Doclet {
    private Reporter reporter;
    private DocletEnvironment env;
    private DocTrees trees;
    private Elements elements;
    private Types types;
    private Document xml;
    private org.w3c.dom.Element root;
    private Path output;
    private final Set<String> warnings = new TreeSet<>();
    private final Map<Element, Map<String, Part>> comments = new HashMap<>();
    private record Part(Element owner, String label, List<? extends DocTree> trees) {}

    public void init(Locale locale, Reporter reporter) { this.reporter = reporter; }
    public String getName() { return "SphinxDoclet"; }
    public SourceVersion getSupportedSourceVersion() { return SourceVersion.latestSupported(); }
    public Set<? extends Option> getSupportedOptions() {
        return Set.of(new Option() {
            public int getArgumentCount() { return 1; }
            public String getDescription() { return "Write versioned Sphinx API XML"; }
            public Kind getKind() { return Kind.STANDARD; }
            public List<String> getNames() { return List.of("--sphinx-output"); }
            public String getParameters() { return "file"; }
            public boolean process(String name, List<String> arguments) {
                output = Path.of(arguments.getFirst()); return true;
            }
        });
    }

    public boolean run(DocletEnvironment environment) {
        env = environment;
        trees = env.getDocTrees(); elements = env.getElementUtils(); types = env.getTypeUtils();
        if (output == null) {
            reporter.print(Diagnostic.Kind.ERROR, "--sphinx-output is required"); return false;
        }
        try {
            xml = DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument();
            root = xml.createElement("api"); xml.appendChild(root);
            root.setAttribute("schema", "1"); root.setAttribute("extractor", "0.1.0");
            var included = env.getIncludedElements().stream()
                .filter(e -> e instanceof TypeElement && visible(e) && !hidden(e))
                .map(e -> (TypeElement)e)
                .sorted(Comparator.comparing(t -> t.getQualifiedName().toString())).toList();
            var packages = new TreeMap<String, PackageElement>();
            for (var t : included) packages.put(elements.getPackageOf(t).toString(), elements.getPackageOf(t));
            for (var p : packages.values()) {
                var n = add(root, "package"); n.setAttribute("name", p.getQualifiedName().toString());
                documentation(n, p);
            }
            for (var t : included) {
                var n = declaration(root, "type", t);
                for (var member : t.getEnclosedElements().stream()
                        .filter(e -> !(e instanceof TypeElement) && visible(e) && !hidden(e))
                        .filter(e -> e instanceof ExecutableElement || e instanceof VariableElement)
                        .sorted(Comparator.comparing(this::id)).toList()) {
                    declaration(n, "member", member);
                }
            }
            for (var warning : warnings) text(root, "diagnostic", warning);
            var transformer = TransformerFactory.newInstance().newTransformer();
            transformer.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
            transformer.setOutputProperty(OutputKeys.INDENT, "yes");
            transformer.transform(new DOMSource(xml), new StreamResult(output.toFile()));
            return true;
        } catch (Exception e) {
            reporter.print(Diagnostic.Kind.ERROR, "Sphinx extraction failed: " + e); return false;
        }
    }

    private boolean visible(Element e) {
        while (e instanceof TypeElement || e instanceof ExecutableElement || e instanceof VariableElement) {
            if (!e.getModifiers().contains(Modifier.PUBLIC) && !e.getModifiers().contains(Modifier.PROTECTED)) return false;
            e = e.getEnclosingElement();
        }
        return true;
    }
    private boolean hidden(Element e) {
        var c = trees.getDocCommentTree(e);
        return c != null && c.getBlockTags().stream().anyMatch(t -> t.getKind() == DocTree.Kind.HIDDEN);
    }
    private org.w3c.dom.Element add(org.w3c.dom.Element parent, String tag) {
        var child = xml.createElement(tag); parent.appendChild(child); return child;
    }
    private void text(org.w3c.dom.Element parent, String tag, String value) {
        var child = add(parent, tag); child.appendChild(xml.createTextNode(value));
    }
    private void warn(Element owner, String message) { warnings.add(id(owner) + ": " + message); }
    private String join(Collection<?> values) {
        return values.stream().map(Object::toString).collect(Collectors.joining(", "));
    }
    private String id(Element e) {
        if (e instanceof QualifiedNameable q) return q.getQualifiedName().toString();
        String base = id(e.getEnclosingElement()) + "#" + e.getSimpleName();
        if (e instanceof ExecutableElement m) {
            base += "(" + m.getParameters().stream().map(p -> linkType(types.erasure(p.asType())))
                .collect(Collectors.joining(",")) + ")";
        }
        return base;
    }
    private String linkType(TypeMirror type) {
        if (type instanceof ArrayType array) return linkType(array.getComponentType()) + "[]";
        if (type instanceof TypeVariable variable) return variable.asElement().getSimpleName().toString();
        if (type instanceof DeclaredType declared) return ((TypeElement)declared.asElement()).getQualifiedName().toString();
        return type.getKind().isPrimitive() ? type.getKind().name().toLowerCase(Locale.ROOT) : type.toString();
    }
    private String typeParameters(List<? extends TypeParameterElement> parameters) {
        if (parameters.isEmpty()) return "";
        return "<" + parameters.stream().map(p -> p.getSimpleName() +
            (p.getBounds().toString().equals("java.lang.Object") ? "" : " extends " +
             p.getBounds().stream().map(Object::toString).collect(Collectors.joining(" & "))))
            .collect(Collectors.joining(", ")) + ">";
    }
    private String annotations(Element e) {
        return e.getAnnotationMirrors().isEmpty() ? "" :
            e.getAnnotationMirrors().stream().map(Object::toString).collect(Collectors.joining(" ")) + " ";
    }
    private String signature(Element e) {
        String mods = e.getModifiers().stream().map(Object::toString).collect(Collectors.joining(" "));
        String prefix = annotations(e) + (mods.isEmpty() ? "" : mods + " ");
        if (e instanceof TypeElement t) {
            String kind = t.getKind() == ElementKind.ANNOTATION_TYPE ? "@interface" : t.getKind().name().toLowerCase(Locale.ROOT);
            String s = prefix + kind + " " + t.getQualifiedName() + typeParameters(t.getTypeParameters());
            if (t.getKind() == ElementKind.RECORD) s += "(" + t.getRecordComponents().stream()
                .map(c -> annotations(c) + c.asType() + " " + c.getSimpleName()).collect(Collectors.joining(", ")) + ")";
            if (t.getKind() == ElementKind.CLASS && t.getSuperclass().getKind() != TypeKind.NONE && !t.getSuperclass().toString().equals("java.lang.Object"))
                s += " extends " + t.getSuperclass();
            if (!t.getInterfaces().isEmpty()) s += (t.getKind().isInterface() ? " extends " : " implements ") + join(t.getInterfaces());
            if (!t.getPermittedSubclasses().isEmpty()) s += " permits " + join(t.getPermittedSubclasses());
            return s;
        }
        if (e instanceof ExecutableElement m) {
            String s = prefix;
            if (!m.getTypeParameters().isEmpty()) s += typeParameters(m.getTypeParameters()) + " ";
            s += m.getKind() == ElementKind.CONSTRUCTOR ? m.getEnclosingElement().getSimpleName() : m.getReturnType() + " " + m.getSimpleName();
            var params = new ArrayList<String>();
            for (int i = 0; i < m.getParameters().size(); i++) {
                var p = m.getParameters().get(i); String type = p.asType().toString();
                if (m.isVarArgs() && i == m.getParameters().size() - 1) type = type.substring(0, type.length() - 2) + "...";
                params.add(annotations(p) + type + " " + p.getSimpleName());
            }
            s += "(" + String.join(", ", params) + ")";
            if (!m.getThrownTypes().isEmpty()) s += " throws " + join(m.getThrownTypes());
            if (m.getDefaultValue() != null) s += " default " + m.getDefaultValue();
            return s;
        }
        var v = (VariableElement)e;
        return prefix + v.asType() + " " + v.getSimpleName() +
            (v.getConstantValue() == null ? "" : " = " + elements.getConstantExpression(v.getConstantValue()));
    }
    private org.w3c.dom.Element declaration(org.w3c.dom.Element parent, String tag, Element e) {
        var n = add(parent, tag);
        n.setAttribute("id", id(e)); n.setAttribute("name", e.getSimpleName().toString());
        n.setAttribute("kind", e.getKind().name().toLowerCase(Locale.ROOT));
        n.setAttribute("visibility", e.getModifiers().contains(Modifier.PUBLIC) ? "public" : "protected");
        n.setAttribute("package", elements.getPackageOf(e).getQualifiedName().toString());
        n.setAttribute("signature", signature(e));
        documentation(n, e); return n;
    }

    private Map<String, Part> parts(Element e) {
        if (comments.containsKey(e)) return comments.get(e);
        var result = new LinkedHashMap<String, Part>(); comments.put(e, result);
        var c = trees.getDocCommentTree(e);
        if (c == null) return result;
        if (elements.getDocCommentKind(e) == Elements.DocCommentKind.END_OF_LINE)
            warn(e, "Markdown documentation comments are not supported; use traditional /** comments for this release.");
        if (!c.getFullBody().isEmpty()) result.put("body", new Part(e, "", c.getFullBody()));
        int see = 0;
        for (var t : c.getBlockTags()) {
            if (t instanceof ParamTree p) {
                String name = p.getName().toString(); String key = "param:" + name;
                if (e instanceof ExecutableElement m) {
                    var params = p.isTypeParameter() ? m.getTypeParameters() : m.getParameters();
                    int index = -1;
                    for (int i = 0; i < params.size(); i++) if (params.get(i).getSimpleName().contentEquals(name)) index = i;
                    if (index < 0) warn(e, "@param " + name + " does not name a declared parameter.");
                    key = (p.isTypeParameter() ? "typeparam:" : "param:") + index;
                }
                result.put(key, new Part(e, p.isTypeParameter() ? "<" + name + ">" : name, p.getDescription()));
            } else if (t instanceof ReturnTree r) result.put("return", new Part(e, "", r.getDescription()));
            else if (t instanceof ThrowsTree r) {
                var target = resolve(e, r.getExceptionName());
                String name = target == null ? r.getExceptionName().toString() : id(target);
                result.put("throws:" + name, new Part(e, name, r.getDescription()));
            } else if (t instanceof SeeTree s) result.put("see:" + see++, new Part(e, "", s.getReference()));
            else if (t instanceof SinceTree s) result.put("since", new Part(e, "", s.getBody()));
            else if (t instanceof DeprecatedTree d) result.put("deprecated", new Part(e, "", d.getBody()));
            else if (t.getKind() != DocTree.Kind.HIDDEN) warn(e, "Unsupported block tag " + t.getKind() + "; retain it in handwritten guides.");
        }
        return result;
    }
    private ExecutableElement overridden(ExecutableElement m) {
        var owner = (TypeElement)m.getEnclosingElement();
        var result = search(m, owner, owner, new HashSet<>());
        if (result != null) return result;
        return search(m, owner, elements.getTypeElement("java.lang.Object"), new HashSet<>());
    }
    private ExecutableElement search(ExecutableElement m, TypeElement owner, TypeElement current, Set<TypeElement> seen) {
        if (!seen.add(current)) return null;
        for (var e : current.getEnclosedElements()) {
            if (e instanceof ExecutableElement p && p.getKind() == ElementKind.METHOD && elements.overrides(m, p, owner)) return p;
        }
        var superclass = types.asElement(current.getSuperclass());
        if (superclass instanceof TypeElement s && !s.getQualifiedName().contentEquals("java.lang.Object")) {
            var found = search(m, owner, s, seen); if (found != null) return found;
        }
        for (var i : current.getInterfaces()) {
            var found = search(m, owner, (TypeElement)types.asElement(i), seen); if (found != null) return found;
        }
        return null;
    }
    private Part findPart(Element e, String key, Set<Element> seen) {
        if (!seen.add(e)) return null;
        Part p = parts(e).get(key);
        if (p != null && !p.trees().isEmpty()) return p;
        if (key.startsWith("throws:")) {
            var requested = elements.getTypeElement(key.substring(7));
            for (var entry : parts(e).entrySet()) {
                if (!entry.getKey().startsWith("throws:")) continue;
                var documented = elements.getTypeElement(entry.getKey().substring(7));
                if (requested != null && documented != null && types.isSubtype(requested.asType(), documented.asType())) return entry.getValue();
            }
        }
        if (e instanceof ExecutableElement m && e.getKind() == ElementKind.METHOD) {
            var parent = overridden(m);
            if (parent != null) return findPart(parent, key, seen);
        }
        return null;
    }
    private void documentation(org.w3c.dom.Element node, Element e) {
        var doc = add(node, "doc");
        var own = parts(e);
        var keys = new LinkedHashSet<>(own.keySet()); keys.add("body");
        boolean overrides = e instanceof ExecutableElement m && m.getKind() == ElementKind.METHOD && trees.getTree(e) != null && overridden(m) != null;
        if (overrides) {
            var m = (ExecutableElement)e;
            for (int i = 0; i < m.getParameters().size(); i++) keys.add("param:" + i);
            for (int i = 0; i < m.getTypeParameters().size(); i++) keys.add("typeparam:" + i);
            if (m.getReturnType().getKind() != TypeKind.VOID) keys.add("return");
            for (var t : m.getThrownTypes()) keys.add("throws:" + types.erasure(t));
        }
        for (var key : keys) {
            Part part = own.get(key);
            if (part == null && overrides) part = findPart(e, key, new HashSet<>());
            if (part == null) {
                if (overrides) warn(e, "Cannot inherit " + key + "; provide the overridden method's source documentation or document this part explicitly.");
                continue;
            }
            var p = add(doc, "part"); p.setAttribute("kind", key.split(":", 2)[0]);
            String label = part.label();
            if (e instanceof ExecutableElement m && (key.startsWith("param:") || key.startsWith("typeparam:"))) {
                int index = Integer.parseInt(key.split(":")[1]);
                var params = key.startsWith("typeparam:") ? m.getTypeParameters() : m.getParameters();
                if (index >= 0 && index < params.size()) label = params.get(index).getSimpleName().toString();
                if (key.startsWith("typeparam:")) label = "<" + label + ">";
            }
            p.setAttribute("label", label);
            emit(p, part.owner(), key, part.trees(), new HashSet<>());
        }
    }
    private Element resolve(Element owner, DocTree reference) {
        var c = trees.getDocCommentTree(owner);
        var path = trees.getPath(owner);
        if (c == null || path == null) return null;
        var docPath = DocTreePath.getPath(new DocTreePath(path, c), reference);
        return docPath == null ? null : trees.getElement(docPath);
    }
    private void reference(org.w3c.dom.Element parent, Element owner, ReferenceTree ref, List<? extends DocTree> label, boolean plain) {
        if (ref == null) {
            warn(owner, "Malformed Javadoc: link is missing a reference target.");
            text(parent, "literal", "[missing link target]"); return;
        }
        var n = add(parent, "link"); n.setAttribute("plain", Boolean.toString(plain));
        var target = resolve(owner, ref);
        n.setAttribute("target", target == null ? ref.toString() : id(target));
        if (target == null) warn(owner, "Unresolved Javadoc reference " + ref + "; check spelling, source paths and classpath.");
        else {
            n.setAttribute("role", target instanceof TypeElement ? "type" : target instanceof ExecutableElement ? "method" : target instanceof PackageElement ? "package" : "field");
            Element type = target;
            while (!(type instanceof TypeElement) && !(type instanceof PackageElement) && type != null) type = type.getEnclosingElement();
            if (type != null) {
                String pkg = elements.getPackageOf(type).getQualifiedName().toString();
                String path = pkg.isEmpty() ? "" : pkg.replace('.', '/') + "/";
                path += type instanceof TypeElement t ? t.getQualifiedName().toString().substring(pkg.isEmpty() ? 0 : pkg.length() + 1) + ".html" : "package-summary.html";
                n.setAttribute("path", path);
                var module = elements.getModuleOf(type);
                n.setAttribute("module", module == null || module.isUnnamed() ? "" : module.getQualifiedName().toString());
                String fragment = "";
                if (target instanceof ExecutableElement m) {
                    fragment = m.getSimpleName() + "(" + m.getParameters().stream()
                        .map(p -> linkType(p.asType())).collect(Collectors.joining(",")) + ")";
                    if (m.isVarArgs()) fragment = fragment.substring(0, fragment.length() - 3) + "...)";
                } else if (target instanceof VariableElement) fragment = target.getSimpleName().toString();
                n.setAttribute("fragment", fragment);
            }
        }
        if (label.isEmpty()) text(n, "text", ref.toString());
        else emit(n, owner, "label", label, new HashSet<>());
    }
    private void emit(org.w3c.dom.Element parent, Element owner, String key, List<? extends DocTree> content, Set<String> chain) {
        for (var t : content) {
            if (t instanceof ErroneousTree v) {
                warn(owner, "Malformed Javadoc: " + v.getDiagnostic().getMessage(Locale.ROOT));
                text(parent, "literal", v.getBody());
            } else if (t instanceof TextTree v) text(parent, "text", v.getBody());
            else if (t instanceof LiteralTree v) text(parent, t.getKind() == DocTree.Kind.CODE ? "code" : "literal", v.getBody().getBody());
            else if (t instanceof EntityTree v) text(parent, "text", Objects.requireNonNullElse(trees.getCharacters(v), v.toString()));
            else if (t instanceof LinkTree l) reference(parent, owner, l.getReference(), l.getLabel(), t.getKind() == DocTree.Kind.LINK_PLAIN);
            else if (t instanceof ReferenceTree r) reference(parent, owner, r, List.of(), false);
            else if (t instanceof StartElementTree s) {
                var n = add(parent, "start"); n.setAttribute("name", s.getName().toString());
                n.setAttribute("closed", Boolean.toString(s.isSelfClosing()));
                for (var a : s.getAttributes()) {
                    if (a instanceof AttributeTree attr) {
                        var x = add(n, "attr"); x.setAttribute("name", attr.getName().toString());
                        x.setTextContent(attr.getValue().stream().map(Object::toString).collect(Collectors.joining()));
                    }
                }
            } else if (t instanceof EndElementTree s) add(parent, "end").setAttribute("name", s.getName().toString());
            else if (t instanceof InheritDocTree inherit) {
                if (!(owner instanceof ExecutableElement m) || m.getKind() != ElementKind.METHOD || !(key.equals("body") || key.equals("return") || key.startsWith("param:") || key.startsWith("typeparam:") || key.startsWith("throws:"))) {
                    warn(owner, "inheritDoc is only valid in overriding method descriptions, parameters, returns and throws.");
                    text(parent, "literal", "[unresolved inheritDoc]"); continue;
                }
                ExecutableElement ancestor = overridden(m);
                if (inherit.getSupertype() != null) {
                    var specified = resolve(owner, inherit.getSupertype()); ancestor = null;
                    if (specified instanceof TypeElement s) ancestor = search(m, (TypeElement)m.getEnclosingElement(), s, new HashSet<>());
                }
                String step = id(owner) + ":" + key;
                Part inherited = ancestor == null ? null : findPart(ancestor, key, new HashSet<>());
                if (inherited == null || !chain.add(step)) {
                    warn(owner, "Cannot resolve inheritDoc for " + key + "; provide ancestor source documentation or write this part explicitly.");
                    text(parent, "literal", "[unresolved inheritDoc]");
                } else {
                    emit(parent, inherited.owner(), key, inherited.trees(), chain); chain.remove(step);
                }
            } else if (t instanceof ReturnTree r) emit(parent, owner, "return", r.getDescription(), chain);
            else if (t.getKind() != DocTree.Kind.COMMENT) {
                warn(owner, "Unsupported Javadoc construct " + t.getKind() + "; use traditional text or <pre>{@code ...}</pre> (snippet and Markdown expansion are deferred).");
                text(parent, "literal", t.toString());
            }
        }
    }
}
