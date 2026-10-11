package demo;
import java.time.Instant;
/** A timestamped location.
 * @param x horizontal coordinate
 * @param at time supplied by the standard-library dependency
 */
public record Point(int x, Instant at) {}
