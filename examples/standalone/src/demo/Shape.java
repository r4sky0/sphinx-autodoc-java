package demo;
/** Something with a position; only {@link Point} implements it. */
public sealed interface Shape permits Point {
    /** Returns the horizontal coordinate.
     * @return the coordinate
     */
    int x();
}
