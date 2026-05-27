import { useState, useEffect, type ReactNode } from 'react';
import { useBackendAPI } from '../hooks/useBackendAPI';
import { useToast } from '../components/Toast';
import { Icon } from '../components/ui/Icon';
import type { Settings as SettingsType, Course, WatchFolder } from '../types/api';

type SettingsTab = 'general' | 'courses' | 'classification' | 'about';

export function Settings() {
  const { getSettings, updateSettings, getCoursesList, getWatchFolders, addWatchFolder, deleteWatchFolder } = useBackendAPI();
  const { addToast } = useToast();
  const [tab, setTab] = useState<SettingsTab>('general');
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [watchFolders, setWatchFolders] = useState<WatchFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isAddingFolder, setIsAddingFolder] = useState(false);
  const [newFolderPath, setNewFolderPath] = useState('');
  const [organizationStyle, setOrganizationStyle] = useState<'week' | 'type'>('week');
  const [confidenceAuto, setConfidenceAuto] = useState(0.9);
  const [confidenceSuggest, setConfidenceSuggest] = useState(0.7);
  const [downloadsPath, setDownloadsPath] = useState('');

  const loadData = async () => {
    setLoading(true);
    const [settingsData, coursesData, foldersData] = await Promise.all([
      getSettings(),
      getCoursesList(),
      getWatchFolders(),
    ]);
    if (settingsData) {
      setSettings(settingsData);
      setOrganizationStyle(settingsData.organization_style);
      setConfidenceAuto(settingsData.confidence_auto);
      setConfidenceSuggest(settingsData.confidence_suggest);
      setDownloadsPath(settingsData.downloads_path || '~/Downloads');
    }
    setCourses(coursesData);
    setWatchFolders(foldersData || []);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    const ok = await updateSettings({
      organization_style: organizationStyle,
      confidence_auto: confidenceAuto,
      confidence_suggest: confidenceSuggest,
    });
    setIsSaving(false);
    if (ok) addToast('Settings saved', 'success');
    else addToast('Failed to save settings', 'error');
  };

  const handleAddFolder = async () => {
    if (!newFolderPath.trim()) {
      addToast('Please enter a folder path', 'error');
      return;
    }
    setIsAddingFolder(true);
    const ok = await addWatchFolder(newFolderPath);
    setIsAddingFolder(false);
    if (ok) {
      setNewFolderPath('');
      await loadData();
      addToast('Watch folder added', 'success');
    } else {
      addToast('Failed to add watch folder', 'error');
    }
  };

  const handleDeleteFolder = async (folderId: number) => {
    const ok = await deleteWatchFolder(folderId);
    if (ok) {
      await loadData();
      addToast('Watch folder removed', 'success');
    } else {
      addToast('Failed to remove watch folder', 'error');
    }
  };

  const tabs: { id: SettingsTab; label: string }[] = [
    { id: 'general', label: 'General' },
    { id: 'courses', label: 'Courses' },
    { id: 'classification', label: 'Classification Rules' },
    { id: 'about', label: 'About' },
  ];

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto animate-pulse h-96 bg-surface-container-low rounded-card" />
    );
  }

  return (
    <div className="max-w-6xl mx-auto w-full pb-12">
      <div className="mb-10">
        <h2 className="font-display text-display-lg-mobile md:text-display-lg text-on-surface">Settings</h2>
        <p className="text-body-md text-on-surface-variant mt-2">
          Manage your preferences, automation rules, and application behavior.
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-8 items-start">
        <nav className="w-full md:w-[240px] flex-shrink-0 md:sticky md:top-6">
          <div className="flex flex-col gap-1">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={
                  tab === t.id
                    ? 'flex items-center justify-between px-4 py-3 bg-surface-variant text-primary rounded-btn border border-outline-variant font-display text-title-sm'
                    : 'flex items-center justify-between px-4 py-3 text-on-surface-variant hover:bg-surface-variant/50 rounded-btn transition-colors text-body-md'
                }
              >
                {t.label}
                {tab === t.id && <Icon name="chevron_right" size={20} />}
              </button>
            ))}
          </div>
        </nav>

        <div className="flex-1 w-full space-y-8">
          {tab === 'general' && (
            <>
              <SettingsSection
                icon="palette"
                title="Appearance"
                description="Scholar Noir dark theme is optimized for late-night study sessions."
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-body-md text-on-surface">Dark Theme</h4>
                    <p className="text-body-sm text-on-surface-variant">Always on — matches your workspace design.</p>
                  </div>
                  <Toggle checked readOnly />
                </div>
              </SettingsSection>

              <SettingsSection
                icon="folder_managed"
                title="Watch Folders"
                description="Directories monitored for automatic sorting."
              >
                <div className="space-y-3">
                  {watchFolders.length === 0 ? (
                    <p className="text-body-sm text-on-surface-variant italic">No watch folders configured yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {watchFolders.map((folder) => (
                        <div
                          key={folder.id}
                          className="flex items-center justify-between p-3 rounded-btn bg-surface border border-outline-variant hover:border-outline transition-colors group"
                        >
                          <div className="flex items-center gap-3 overflow-hidden flex-1">
                            <Icon
                              name={folder.enabled ? 'folder' : 'folder_off'}
                              size={20}
                              className={folder.enabled ? 'text-on-surface-variant' : 'text-outline-variant'}
                            />
                            <span className="font-mono text-code-path text-secondary truncate">{folder.path}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleDeleteFolder(folder.id)}
                            className="ml-3 p-1.5 text-error hover:bg-error/10 rounded transition-colors"
                            title="Remove watch folder"
                          >
                            <Icon name="delete" size={20} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="pt-4 border-t border-outline-variant">
                    <label className="block text-body-sm font-medium text-on-surface mb-2">Add Watch Folder</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="e.g., ~/Documents/Courses or /home/user/Downloads"
                        value={newFolderPath}
                        onChange={(e) => setNewFolderPath(e.target.value)}
                        disabled={isAddingFolder}
                        className="flex-1 px-4 py-3 rounded-btn bg-surface border border-outline-variant focus:border-primary focus:outline-none transition-colors text-body-md text-on-surface placeholder:text-on-surface-variant"
                      />
                      <button
                        type="button"
                        onClick={handleAddFolder}
                        disabled={isAddingFolder}
                        className="btn-primary"
                      >
                        {isAddingFolder ? 'Adding…' : 'Add'}
                      </button>
                    </div>
                  </div>

                  {settings?.semester_name && (
                    <p className="text-body-sm text-on-surface-variant">
                      Active semester: <span className="text-primary">{settings.semester_name}</span>
                    </p>
                  )}
                </div>
              </SettingsSection>
            </>
          )}

          {tab === 'courses' && (
            <SettingsSection icon="school" title="Courses" description={`${courses.length} courses loaded for classification.`}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-80 overflow-y-auto">
                {courses.map((c) => (
                  <div key={c.id} className="p-3 bg-surface border border-outline-variant rounded-btn">
                    <p className="text-body-sm font-medium text-on-surface">{c.code}</p>
                    <p className="text-body-sm text-on-surface-variant truncate">{c.name}</p>
                  </div>
                ))}
              </div>
            </SettingsSection>
          )}

          {tab === 'classification' && (
            <SettingsSection
              icon="smart_toy"
              title="Automation Behavior"
              description="Configure how AcadSort processes incoming documents."
            >
              <div className="space-y-8">
                <div>
                  <h4 className="text-body-md text-on-surface mb-3">Organization Method</h4>
                  <div className="flex gap-3 flex-wrap">
                    {(['week', 'type'] as const).map((style) => (
                      <button
                        key={style}
                        type="button"
                        onClick={() => setOrganizationStyle(style)}
                        className={`px-4 py-3 rounded-btn border transition-colors ${
                          organizationStyle === style
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-outline-variant text-on-surface-variant hover:border-outline'
                        }`}
                      >
                        {style === 'week' ? 'By Week' : 'By Type'}
                      </button>
                    ))}
                  </div>
                </div>

                <SliderField
                  label="Auto-Move Threshold"
                  hint={`Files at ${Math.round(confidenceAuto * 100)}%+ confidence move automatically`}
                  value={confidenceAuto}
                  min={0.5}
                  max={1}
                  step={0.05}
                  onChange={setConfidenceAuto}
                />
                <SliderField
                  label="Suggest Threshold"
                  hint={`Files at ${Math.round(confidenceSuggest * 100)}%+ go to review queue`}
                  value={confidenceSuggest}
                  min={0.3}
                  max={0.9}
                  step={0.05}
                  onChange={setConfidenceSuggest}
                />
              </div>

              <div className="mt-8 pt-6 border-t border-outline-variant flex justify-end gap-3">
                <button type="button" onClick={loadData} className="btn-ghost">
                  Discard Changes
                </button>
                <button type="button" onClick={handleSave} disabled={isSaving} className="btn-primary">
                  {isSaving ? 'Saving…' : 'Save Configuration'}
                </button>
              </div>
            </SettingsSection>
          )}

          {tab === 'about' && (
            <SettingsSection icon="info" title="About AcadSort" description="Local-first academic file organizer for UP Tacloban.">
              <ul className="text-body-sm text-on-surface-variant space-y-2 list-disc pl-5">
                <li>Watches Downloads and classifies academic files locally</li>
                <li>No internet required for organization — data stays on your device</li>
                <li>Powered by multilingual embeddings and optional Ollama LLM fallback</li>
              </ul>
              <p className="font-mono text-code-path text-outline mt-4">v0.1.0 · Scholar Noir UI</p>
            </SettingsSection>
          )}
        </div>
      </div>
    </div>
  );
}

function SettingsSection({
  icon,
  title,
  description,
  children,
}: {
  icon: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="card-surface p-6">
      <div className="border-b border-outline-variant pb-4 mb-6">
        <h3 className="font-display text-title-sm text-on-surface flex items-center gap-2">
          <Icon name={icon} size={22} className="text-primary" />
          {title}
        </h3>
        <p className="text-body-sm text-on-surface-variant mt-1">{description}</p>
      </div>
      {children}
    </section>
  );
}

function Toggle({ checked, readOnly, onChange }: { checked: boolean; readOnly?: boolean; onChange?: () => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={readOnly}
      onClick={onChange}
      className={`relative inline-flex h-6 w-11 rounded-full border-2 border-transparent transition-colors ${
        checked ? 'bg-primary' : 'bg-surface-variant'
      }`}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-surface-container shadow transition ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`}
      />
    </button>
  );
}

function SliderField({
  label,
  hint,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  hint: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="pt-4 border-t border-outline-variant/50">
      <div className="flex justify-between mb-2">
        <h4 className="text-body-md text-on-surface">{label}</h4>
        <span className="text-body-sm text-primary font-semibold">{Math.round(value * 100)}%</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(parseFloat(e.target.value))} />
      <p className="text-body-sm text-on-surface-variant mt-2">{hint}</p>
    </div>
  );
}
