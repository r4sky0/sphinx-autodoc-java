package demo;
/** Execution mode. */
public enum Mode {
    /** Quick processing. */ FAST,
    /** Careful processing. */ CAREFUL;
    /** Returns whether this mode is fast.
     * @return true for fast mode
     */
    public boolean isFast() { return this == FAST; }
}
