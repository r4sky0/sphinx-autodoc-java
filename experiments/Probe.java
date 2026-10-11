import com.sun.source.doctree.*;
import com.sun.source.util.*;
import java.util.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import jdk.javadoc.doclet.*;

/** Reproducible API feasibility probe; does not load application classes. */
public class Probe implements Doclet {
    public void init(Locale locale, Reporter reporter) {}
    public String getName() { return "Probe"; }
    public SourceVersion getSupportedSourceVersion() { return SourceVersion.latestSupported(); }
    public Set<? extends Option> getSupportedOptions() { return Set.of(); }
    public boolean run(DocletEnvironment env) {
        var trees = env.getDocTrees();
        for (var e : env.getIncludedElements().stream().sorted(Comparator.comparing(Object::toString)).toList()) {
            if (!(e instanceof TypeElement t)) continue;
            System.out.println(t.getKind() + " " + t.getQualifiedName() + " " + t.getTypeParameters());
            for (var member : t.getEnclosedElements()) {
                System.out.println("  " + member.getKind() + " " + member + " : " + member.asType());
                var comment = trees.getDocCommentTree(member);
                if (comment == null) continue;
                System.out.println("    raw: " + comment);
                new DocTreePathScanner<Void, Void>() {
                    public Void visitReference(ReferenceTree ref, Void unused) {
                        var target = trees.getElement(getCurrentPath());
                        System.out.println("    resolved: " + ref + " -> " + target + " owner=" + (target == null ? "?" : target.getEnclosingElement()));
                        return null;
                    }
                }.scan(new DocTreePath(trees.getPath(member), comment), null);
                if (member instanceof ExecutableElement m) {
                    for (var parent : env.getTypeUtils().directSupertypes(t.asType())) {
                        for (var other : env.getTypeUtils().asElement(parent).getEnclosedElements()) {
                            if (other instanceof ExecutableElement p && env.getElementUtils().overrides(m, p, t))
                                System.out.println("    overrides: " + p + " doc=" + trees.getDocCommentTree(p));
                        }
                    }
                }
            }
        }
        return true;
    }
}
