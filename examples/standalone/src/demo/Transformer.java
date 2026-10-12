package demo;

/** A generic transformation contract.
 * @param <T> input and output type
 * @author Example Author
 * @version 1.0
 */
public interface Transformer<T> {
    /** Transforms a value using {@link Widget#convert(int)} when needed.
     * <p>The result preserves {@literal <angle brackets>}.
     * @param input the value to transform
     * @return the transformed value
     * @throws IllegalArgumentException if the value is invalid
     * @throws IllegalArgumentException if the value is empty
     */
    T convert(T input) throws IllegalArgumentException;

    /** Transforms a value twice.
     * @apiNote Use this when one pass is not enough.
     * @implSpec The default implementation calls {@link #convert(Object)} twice.
     * @implNote This implementation does not cache the first result.
     * @param input the value to transform
     * @return the twice transformed value
     */
    default T twice(T input) {
        return convert(convert(input));
    }
}
