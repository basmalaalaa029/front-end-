import { useEffect, useState } from "react";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { HubHeader } from "@/features/hub-shell";
import { useI18n } from "@/features/i18n";
import api from "@/lib/api";
import type { ProfileData } from "../../types/profile.types";
import "../../styles/profile.scss";

function getInitials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

interface EditModalProps {
  data: ProfileData;
  onClose: () => void;
  onSave: (updated: Partial<ProfileData>) => Promise<void>;
  dir: "rtl" | "ltr";
}

function EditModal({ data, onClose, onSave, dir }: EditModalProps) {
  const [form, setForm] = useState<Partial<ProfileData>>({
    name: data.name,
    phone: data.phone ?? "",
    location: data.location ?? "",
    bio: data.bio ?? "",
    jobTitle: data.jobTitle ?? "",
    skills: data.skills ?? [],
    linkedIn: data.linkedIn ?? "",
    portfolio: data.portfolio ?? "",
  });
  const [skillInput, setSkillInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (field: keyof ProfileData, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const addSkill = () => {
    const trimmed = skillInput.trim();
    if (!trimmed) return;
    setForm((prev) => ({
      ...prev,
      skills: [...(prev.skills ?? []), trimmed],
    }));
    setSkillInput("");
  };

  const removeSkill = (idx: number) =>
    setForm((prev) => ({
      ...prev,
      skills: (prev.skills ?? []).filter((_, i) => i !== idx),
    }));

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await onSave(form);
      onClose();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } } };
      setError(ax.response?.data?.message ?? "حدث خطأ، حاول مرة أخرى.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-modal-overlay" onClick={onClose} dir={dir}>
      <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
        <div className="profile-modal__header">
          <h2 className="profile-modal__title">تعديل البروفايل</h2>
          <button type="button" className="profile-modal__close" onClick={onClose} aria-label="إغلاق">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M4 4l10 10M14 4L4 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="profile-modal__body">
          <div className="profile-hub-form-group">
            <label className="profile-hub-label">الاسم الكامل</label>
            <input
              className="profile-hub-input"
              value={form.name ?? ""}
              onChange={(e) => set("name", e.target.value)}
              placeholder="أحمد محمد"
            />
          </div>

          <div className="profile-hub-form-group">
            <label className="profile-hub-label">المسمى الوظيفي</label>
            <input
              className="profile-hub-input"
              value={form.jobTitle ?? ""}
              onChange={(e) => set("jobTitle", e.target.value)}
              placeholder="مطور Full Stack"
            />
          </div>

          <div className="profile-hub-form-row">
            <div className="profile-hub-form-group">
              <label className="profile-hub-label">رقم الهاتف</label>
              <input
                className="profile-hub-input"
                value={form.phone ?? ""}
                onChange={(e) => set("phone", e.target.value)}
                placeholder="+20 10 0000 0000"
              />
            </div>
            <div className="profile-hub-form-group">
              <label className="profile-hub-label">الموقع</label>
              <input
                className="profile-hub-input"
                value={form.location ?? ""}
                onChange={(e) => set("location", e.target.value)}
                placeholder="القاهرة، مصر"
              />
            </div>
          </div>

          <div className="profile-hub-form-group">
            <label className="profile-hub-label">نبذة شخصية</label>
            <textarea
              className="profile-hub-input profile-hub-textarea"
              value={form.bio ?? ""}
              onChange={(e) => set("bio", e.target.value)}
              placeholder="اكتب نبذة قصيرة عن نفسك..."
              rows={3}
            />
          </div>

          <div className="profile-hub-form-group">
            <label className="profile-hub-label">المهارات</label>
            <div className="profile-hub-skill-row">
              <input
                className="profile-hub-input"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
                placeholder="اكتب مهارة واضغط Enter"
              />
              <button type="button" className="btn btn-secondary btn-sm" onClick={addSkill}>
                إضافة
              </button>
            </div>
            <div className="profile-hub-skill-tags">
              {(form.skills ?? []).map((s, i) => (
                <span key={i} className="profile-hub-skill-tag">
                  {s}
                  <button type="button" onClick={() => removeSkill(i)} aria-label="حذف">
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          <div className="profile-hub-form-group">
            <label className="profile-hub-label">LinkedIn</label>
            <input
              className="profile-hub-input"
              value={form.linkedIn ?? ""}
              onChange={(e) => set("linkedIn", e.target.value)}
              placeholder="https://linkedin.com/in/username"
            />
          </div>
          <div className="profile-hub-form-group">
            <label className="profile-hub-label">Portfolio / GitHub</label>
            <input
              className="profile-hub-input"
              value={form.portfolio ?? ""}
              onChange={(e) => set("portfolio", e.target.value)}
              placeholder="https://github.com/username"
            />
          </div>

          {error ? <p className="profile-hub-form-error">{error}</p> : null}
        </div>

        <div className="profile-modal__footer">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
            إلغاء
          </button>
          <button type="button" className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
            {loading ? (
              <span className="profile-hub-spinner" />
            ) : (
              <>
                <SaveIcon />
                حفظ التغييرات
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

const EditIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
    <path d="M10.5 2.5l2 2-8 8H2.5v-2l8-8z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
  </svg>
);
const SaveIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
    <path d="M2 8l4 4 7-7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);
const LocationIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
    <path d="M7 1a4 4 0 014 4c0 3-4 8-4 8S3 8 3 5a4 4 0 014-4z" stroke="currentColor" strokeWidth="1.3" />
    <circle cx="7" cy="5" r="1.3" stroke="currentColor" strokeWidth="1.3" />
  </svg>
);
const PhoneIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
    <path d="M2 2h3l1.5 3-1.5 1a7 7 0 003 3l1-1.5 3 1.5v3a1 1 0 01-1 1A11 11 0 011 3a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.2" />
  </svg>
);
const LinkIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
    <path d="M5.5 8.5a3 3 0 004.243 0l2-2a3 3 0 00-4.243-4.243L6.5 3.25" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    <path d="M8.5 5.5a3 3 0 00-4.243 0l-2 2a3 3 0 004.243 4.243L7.5 10.75" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
  </svg>
);

export default function Profile() {
  const { token } = useAuthStore();
  const { isRtl } = useI18n();
  const dir = isRtl ? "rtl" : "ltr";

  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);

  useEffect(() => {
    if (!token) return;

    const fetchProfile = async () => {
      try {
        setLoading(true);
        setError(null);
        const { data } = await api.get<ProfileData>("/users/profile");
        setProfile(data);
      } catch (err: unknown) {
        const ax = err as { response?: { data?: { message?: string } } };
        setError(ax.response?.data?.message ?? "تعذّر تحميل البروفايل.");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [token]);

  const handleSave = async (updated: Partial<ProfileData>) => {
    const { data } = await api.put<ProfileData>("/users/profile", updated);
    setProfile(data);
  };

  if (loading) {
    return (
      <>
        <HubHeader title="Profile" sub="Loading…" />
        <div className="profile-hub-body" dir={dir}>
          <div className="card profile-hub-loading">
            <div className="profile-hub-skeleton profile-hub-skeleton--avatar" />
            <div className="profile-hub-skeleton profile-hub-skeleton--line" />
            <div className="profile-hub-skeleton profile-hub-skeleton--line profile-hub-skeleton--short" />
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <HubHeader title="Profile" />
        <div className="profile-hub-body" dir={dir}>
          <div className="profile-hub-error card" style={{ padding: "2rem" }}>
            <p style={{ margin: 0, color: "var(--fg-secondary)" }}>{error}</p>
            <button type="button" className="btn btn-secondary" onClick={() => window.location.reload()}>
              إعادة المحاولة
            </button>
          </div>
        </div>
      </>
    );
  }

  if (!profile) return null;

  return (
    <>
      <HubHeader
        title="Profile"
        sub={profile.email}
        right={
          <button type="button" className="btn btn-primary" onClick={() => setEditOpen(true)}>
            <EditIcon />
            تعديل البروفايل
          </button>
        }
      />
      <div className="profile-hub-body" dir={dir}>
        <section className="card profile-hub-main">
          <div className="profile-hub-avatar-wrap">
            {profile.avatarUrl ? (
              <img src={profile.avatarUrl} alt={profile.name} className="profile-hub-avatar" />
            ) : (
              <div className="profile-hub-avatar profile-hub-avatar--initials">{getInitials(profile.name)}</div>
            )}
          </div>

          <div className="profile-hub-info">
            <div className="profile-hub-name-row">
              <h1 className="profile-hub-name">{profile.name}</h1>
            </div>

            {profile.jobTitle ? <p className="profile-hub-job">{profile.jobTitle}</p> : null}

            <p className="profile-hub-email">{profile.email}</p>

            <div className="profile-hub-meta">
              {profile.location ? (
                <span className="profile-hub-meta-item">
                  <LocationIcon />
                  {profile.location}
                </span>
              ) : null}
              {profile.phone ? (
                <span className="profile-hub-meta-item">
                  <PhoneIcon />
                  {profile.phone}
                </span>
              ) : null}
              {profile.linkedIn ? (
                <a
                  href={profile.linkedIn}
                  target="_blank"
                  rel="noreferrer"
                  className="profile-hub-meta-item profile-hub-meta-link"
                >
                  <LinkIcon />
                  LinkedIn
                </a>
              ) : null}
              {profile.portfolio ? (
                <a
                  href={profile.portfolio}
                  target="_blank"
                  rel="noreferrer"
                  className="profile-hub-meta-item profile-hub-meta-link"
                >
                  <LinkIcon />
                  Portfolio
                </a>
              ) : null}
            </div>
          </div>
        </section>

        {profile.bio ? (
          <section className="card profile-hub-section">
            <h2 className="profile-hub-section-title">نبذة شخصية</h2>
            <p className="profile-hub-section-text">{profile.bio}</p>
          </section>
        ) : null}

        {profile.skills && profile.skills.length > 0 ? (
          <section className="card profile-hub-section">
            <h2 className="profile-hub-section-title">المهارات</h2>
            <div className="profile-hub-skill-tags">
              {profile.skills.map((skill, i) => (
                <span key={i} className="profile-hub-skill-tag profile-hub-skill-tag--readonly">
                  {skill}
                </span>
              ))}
            </div>
          </section>
        ) : null}

        {editOpen ? (
          <EditModal data={profile} onClose={() => setEditOpen(false)} onSave={handleSave} dir={dir} />
        ) : null}
      </div>
    </>
  );
}
