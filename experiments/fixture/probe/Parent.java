package probe;
/** A generic parent. */
public interface Parent<T> {
    /** Transforms a value. See {@link Sample#convert(int)}.
     * @param input the input value
     * @return the transformed value
     */
    T convert(T input);
}
