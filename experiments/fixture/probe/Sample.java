package probe;
import java.time.Instant;
/** Probe for {@link Instant} and {@link Sample.Point}. */
public class Sample implements Parent<String> {
    /** {@inheritDoc} */
    @Override public String convert(String renamed) { return renamed; }
    /** Converts a number. */
    public String convert(int number) { return "" + number; }
    /** A modern data carrier. @param at dependency type */
    public record Point(Instant at) {}
}
