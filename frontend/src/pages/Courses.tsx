import { useState, useEffect, useMemo } from 'react';
import { useBackendAPI } from '../hooks/useBackendAPI';
import { courseColor } from '../lib/courseColors';
import type { Course } from '../types/api';

interface CoursesProps {
  searchQuery: string;
}

export function Courses({ searchQuery }: CoursesProps) {
  const { getCoursesList } = useBackendAPI();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCoursesList().then((data) => {
      setCourses(data);
      setLoading(false);
    });
  }, [getCoursesList]);

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return courses;
    return courses.filter(
      (c) => c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q)
    );
  }, [courses, searchQuery]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-3 animate-pulse">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-24 bg-surface-container-low rounded-card" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto w-full">
      <div className="mb-8">
        <h1 className="font-display text-display-lg-mobile md:text-display-lg text-on-surface">Courses</h1>
        <p className="text-body-md text-on-surface-variant mt-2">
          {filtered.length} UP Tacloban course{filtered.length !== 1 ? 's' : ''} in your active semester
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-card-gap">
        {filtered.map((course) => (
          <div key={course.id} className="card-surface-interactive p-5 flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <div
                className="w-2 h-8 rounded-full shrink-0"
                style={{ backgroundColor: courseColor(course.code) }}
              />
              <div className="min-w-0">
                <p className="font-display text-title-sm text-on-surface">{course.code}</p>
                <p className="text-body-sm text-on-surface-variant truncate">{course.name}</p>
              </div>
            </div>
            {course.keywords && course.keywords.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {course.keywords.slice(0, 4).map((kw) => (
                  <span
                    key={kw}
                    className="label-caps text-outline bg-surface-container-highest px-2 py-0.5 rounded-md border border-outline-variant/50"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
