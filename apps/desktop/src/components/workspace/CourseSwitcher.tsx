import { courses } from "@/lib/data/demoData";
import { Icon } from "@/components/ui/Icon";

export function CourseSwitcher() {
  return (
    <button className="course-switcher" type="button">
      <span className="course-switcher-dot" />
      <span>All courses</span>
      <span className="course-switcher-count">{courses.length}</span>
      <Icon name="chevronDown" size={16} />
    </button>
  );
}
