package demo;

/** A generic transformation contract.
 * @param <T> input and output type
 */
public interface Transformer<T> {
    /** Transforms a value using {@link Widget#convert(int)} when needed.
     * <p>The result preserves {@literal <angle brackets>}.
     * @param input the value to transform
     * @return the transformed value
     * @throws IllegalArgumentException if the value is invalid
     */
    T convert(T input) throws IllegalArgumentException;
}
