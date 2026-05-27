import { useState } from 'react';
import { Icon } from '../components/ui/Icon';

const SEMESTER_OPTIONS = [
  '1st Semester 2025-2026',
  '2nd Semester 2024-2025',
  '1st Semester 2024-2025',
  'Midyear 2025',
];

interface SetupWizardProps {
  onComplete: (semesterName: string, organizationStyle: 'week' | 'type') => void;
  onCancel?: () => void;
}

export function SetupWizard({ onComplete, onCancel }: SetupWizardProps) {
  const [step, setStep] = useState(0);
  const [semester, setSemester] = useState('');
  const [organizationStyle, setOrganizationStyle] = useState<'week' | 'type'>('week');
  const [submitting, setSubmitting] = useState(false);

  const handleContinue = async () => {
    if (step === 0 && !semester) return;
    if (step < 1) {
      setStep(1);
      return;
    }
    setSubmitting(true);
    onComplete(semester, organizationStyle);
    setSubmitting(false);
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <main className="w-full max-w-[560px]">
        <div className="text-center mb-12">
          <h1 className="font-display text-display-lg text-primary tracking-tight mb-2">AcadSort</h1>
          <p className="text-body-sm text-on-surface-variant">Workspace Initialization</p>
        </div>

        <div className="bg-surface-container rounded-card border border-outline-variant p-8 shadow-elevated relative overflow-hidden">
          <div className="flex justify-center gap-2 mb-10">
            {[0, 1].map((i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-colors ${i <= step ? 'bg-primary' : 'bg-surface-variant'}`}
              />
            ))}
          </div>

          {step === 0 && (
            <div className="space-y-8 animate-fade-in">
              <div>
                <h2 className="font-display text-headline-md text-on-surface mb-2">
                  What semester are you setting up?
                </h2>
                <p className="text-body-md text-on-surface-variant">
                  Select the current academic term to organize your upcoming files and schedules.
                </p>
              </div>
              <div className="space-y-4">
                <label className="label-caps text-on-surface-variant block" htmlFor="semester">
                  Academic Term
                </label>
                <div className="relative">
                  <select
                    id="semester"
                    value={semester}
                    onChange={(e) => setSemester(e.target.value)}
                    className="input-field appearance-none pr-10"
                  >
                    <option value="">Select a term…</option>
                    {SEMESTER_OPTIONS.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                  <Icon
                    name="expand_more"
                    size={22}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
                  />
                </div>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-8 animate-fade-in">
              <div>
                <h2 className="font-display text-headline-md text-on-surface mb-2">How should files be organized?</h2>
                <p className="text-body-md text-on-surface-variant">
                  Choose your default folder structure for course materials.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {(['week', 'type'] as const).map((style) => (
                  <button
                    key={style}
                    type="button"
                    onClick={() => setOrganizationStyle(style)}
                    className={`p-4 rounded-card border text-left transition-colors ${
                      organizationStyle === style
                        ? 'border-primary bg-primary/10'
                        : 'border-outline-variant hover:border-outline'
                    }`}
                  >
                    <p className="font-display text-title-sm text-on-surface">
                      {style === 'week' ? 'By Week' : 'By Type'}
                    </p>
                    <p className="text-body-sm text-on-surface-variant mt-1">
                      {style === 'week' ? 'Week_01, Week_02…' : 'Lectures, Labs, Exams…'}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="pt-8 flex justify-end gap-4">
            {onCancel && (
              <button type="button" onClick={onCancel} className="btn-secondary border-outline-variant">
                Cancel
              </button>
            )}
            <button
              type="button"
              onClick={handleContinue}
              disabled={(step === 0 && !semester) || submitting}
              className="px-6 py-3 rounded-btn bg-primary-container text-on-primary-container hover:opacity-90 transition-opacity flex items-center gap-2 disabled:opacity-40"
            >
              {submitting ? 'Setting up…' : step === 1 ? 'Finish' : 'Continue'}
              <Icon name="arrow_forward" size={20} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
