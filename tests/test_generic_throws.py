from __future__ import annotations

import pytest
from test_integration import element

from sphinx_java_autodoc.extractor import extract


@pytest.mark.parametrize("explicit", [False, True])
@pytest.mark.parametrize(
    "exception", ["java.io.IOException", "java.io.FileNotFoundException"]
)
def test_generic_throws_inheritance(tmp_path, explicit, exception):
    source = tmp_path / "Child.java"
    description = (
        f"/** @throws {exception} Before {{@inheritDoc Middle}} after. */"
        if explicit
        else ""
    )
    source.write_text(f"""interface Contract<E extends Exception> {{
    /** Perform the operation.
     * @throws E if reading fails; see {{@link java.io.Reader}}
     */
    void run() throws E;
}}
abstract class Middle<F extends Exception> implements Contract<F> {{
    /** {{@inheritDoc}}
     * @throws F {{@inheritDoc}}
     */
    public abstract void run() throws F;
}}
public class Child extends Middle<java.io.IOException> {{
    {description}
    public void run() throws {exception} {{}}
}}
""")
    root = extract([source], [], tmp_path / "cache").root
    assert not root.findall("diagnostic")
    part = element(root, "Child#run()").find("doc/part[@kind='throws']")
    assert part.get("label") == exception.rpartition(".")[2]
    assert part.get("target") == exception
    assert "if reading fails" in "".join(part.itertext())
    assert part.find("link").get("target") == "java.io.Reader"
    if explicit:
        assert "Before" in "".join(part.itertext())
        assert "after." in "".join(part.itertext())


def test_method_exception_type_parameters_are_matched_by_position(tmp_path):
    source = tmp_path / "Child.java"
    source.write_text("""interface Contract {
    /** Perform an operation.
     * @param <E> failure type
     * @throws E if the operation fails
     */
    <E extends Exception> void run() throws E;
}
public class Child implements Contract {
    public <F extends Exception> void run() throws F {}
}
""")
    root = extract([source], [], tmp_path / "cache").root
    assert not root.findall("diagnostic")
    parts = element(root, "Child#run()").findall("doc/part[@kind='throws']")
    assert len(parts) == 1
    assert parts[0].get("label") == "F"
    assert "if the operation fails" in "".join(parts[0].itertext())


def test_generic_throws_does_not_match_an_unrelated_substitution(tmp_path):
    source = tmp_path / "Child.java"
    source.write_text("""interface Contract<E extends Exception> {
    /** Perform an operation.
     * @throws E if reading fails
     */
    void run() throws E;
}
public class Child implements Contract<java.io.IOException> {
    /** Perform the child operation.
     * @throws IllegalArgumentException {@inheritDoc}
     */
    public void run() {}
}
""")
    root = extract([source], [], tmp_path / "cache").root
    assert any(
        "Cannot resolve inheritDoc" in d.text for d in root.findall("diagnostic")
    )
    assert "if reading fails" not in "".join(element(root, "Child#run()").itertext())


def test_distinct_generic_exceptions_keep_their_own_documentation(tmp_path):
    source = tmp_path / "Child.java"
    source.write_text("""interface Contract<A extends Exception, B extends Exception> {
    /** Perform an operation.
     * @throws A first failure
     * @throws B second failure
     */
    void run() throws A, B;
}
/** A generic implementation.
 * @param <X> first failure type
 * @param <Y> second failure type
 */
public class Child<X extends Exception, Y extends Exception> implements Contract<X, Y> {
    /** Perform the child operation.
     * @throws X own first failure
     */
    public void run() throws X, Y {}
}
""")
    root = extract([source], [], tmp_path / "cache").root
    assert not root.findall("diagnostic")
    parts = element(root, "Child#run()").findall("doc/part[@kind='throws']")
    assert [(p.get("label"), "".join(p.itertext()).strip()) for p in parts] == [
        ("X", "own first failure"),
        ("Y", "second failure"),
    ]
