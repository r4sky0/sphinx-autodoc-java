package demo;
import java.lang.annotation.*;
/** A source annotation. */
@Documented
@Retention(RetentionPolicy.SOURCE)
@Target({ElementType.TYPE, ElementType.PARAMETER})
public @interface Label {
    /** Human-readable label.
     * @return label text
     */
    String value() default "default";
}
