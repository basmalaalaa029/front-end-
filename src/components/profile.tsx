import { useEffect, useState } from "react";
import { useAuthStore } from "../lib/store";
import api from "../lib/api";
import "./Profile.scss";

// ── Types ─────────────────────────────────────────────────
interface ProfileData {
  _id: string;
  name: string;
  email: string;
  phone?: string;
  location?: string;
  bio?: string;
  jobTitle?: string;
  avatarUrl?: string;
  skills?: string[];
  linkedIn?: string;
  portfolio?: string;
}

// ── Helpers ───────────────────────────────────────────────
const getInitials = (name: string) =>
  name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

// ── Edit Modal ────────────────────────────────────────────
interface EditModalProps {
  data: ProfileData;
  onClose: () => void;
  onSave: (updated: Partial<ProfileData>) => Promise<void>;
}

function EditModal({ data, onClose, onSave }: EditModalProps) {
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
    } catch (err: any) {
      setError(err?.response?.data?.message ?? "حدث خطأ، حاول مرة أخرى.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} dir="rtl">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2 className="modal__title">تعديل البروفايل</h2>
          <button className="modal__close" onClick={onClose} aria-label="إغلاق">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M4 4l10 10M14 4L4 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="modal__body">
          {/* Name */}
          <div className="form-group">
            <label className="form-label">الاسم الكامل</label>
            <input
              className="form-input"
              value={form.name ?? ""}
              onChange={(e) => set("name", e.target.value)}
              placeholder="أحمد محمد"
            />
          </div>

          {/* Job Title */}
          <div className="form-group">
            <label className="form-label">المسمى الوظيفي</label>
            <input
              className="form-input"
              value={form.jobTitle ?? ""}
              onChange={(e) => set("jobTitle", e.target.value)}
              placeholder="مطور Full Stack"
            />
          </div>

          {/* Phone & Location */}
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">رقم الهاتف</label>
              <input
                className="form-input"
                value={form.phone ?? ""}
                onChange={(e) => set("phone", e.target.value)}
                placeholder="+20 10 0000 0000"
              />
            </div>
            <div className="form-group">
              <label className="form-label">الموقع</label>
              <input
                className="form-input"
                value={form.location ?? ""}
                onChange={(e) => set("location", e.target.value)}
                placeholder="القاهرة، مصر"
              />
            </div>
          </div>

          {/* Bio */}
          <div className="form-group">
            <label className="form-label">نبذة شخصية</label>
            <textarea
              className="form-input form-textarea"
              value={form.bio ?? ""}
              onChange={(e) => set("bio", e.target.value)}
              placeholder="اكتب نبذة قصيرة عن نفسك..."
              rows={3}
            />
          </div>

          {/* Skills */}
          <div className="form-group">
            <label className="form-label">المهارات</label>
            <div className="skill-input-row">
              <input
                className="form-input"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addSkill()}
                placeholder="اكتب مهارة واضغط Enter"
              />
              <button className="btn btn--sm btn--outline" type="button" onClick={addSkill}>
                إضافة
              </button>
            </div>
            <div className="skill-tags">
              {(form.skills ?? []).map((s, i) => (
                <span key={i} className="skill-tag">
                  {s}
                  <button type="button" onClick={() => removeSkill(i)} aria-label="حذف">×</button>
                </span>
              ))}
            </div>
          </div>

          {/* LinkedIn & Portfolio */}
          <div className="form-group">
            <label className="form-label">LinkedIn</label>
            <input
              className="form-input"
              value={form.linkedIn ?? ""}
              onChange={(e) => set("linkedIn", e.target.value)}
              placeholder="https://linkedin.com/in/username"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Portfolio / GitHub</label>
            <input
              className="form-input"
              value={form.portfolio ?? ""}
              onChange={(e) => set("portfolio", e.target.value)}
              placeholder="https://github.com/username"
            />
          </div>

          {error && <p className="form-error">{error}</p>}
        </div>

        <div className="modal__footer">
          <button className="btn btn--outline" onClick={onClose} disabled={loading}>
            إلغاء
          </button>
          <button className="btn btn--primary" onClick={handleSubmit} disabled={loading}>
            {loading ? (
              <span className="spinner" />
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

// ── Small Icons ───────────────────────────────────────────
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

// ── Main Profile Page ─────────────────────────────────────
export default function Profile() {
  const { user, token } = useAuthStore();

  const [profile, setProfile]   = useState<ProfileData | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);

  // ── Fetch profile from backend ──
  useEffect(() => {
    if (!token) return;

    const fetchProfile = async () => {
      try {
        setLoading(true);
        setError(null);
        const { data } = await api.get<ProfileData>("/users/profile");
        setProfile(data);
      } catch (err: any) {
        setError(err?.response?.data?.message ?? "تعذّر تحميل البروفايل.");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [token]);

  // ── Save updated profile to backend ──
  const handleSave = async (updated: Partial<ProfileData>) => {
    const { data } = await api.put<ProfileData>("/users/profile", updated);
    setProfile(data);
  };

  // ── States ────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="profile-loading" dir="rtl">
        <div className="skeleton skeleton--avatar" />
        <div className="skeleton skeleton--line" />
        <div className="skeleton skeleton--line skeleton--short" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-error" dir="rtl">
        <p>{error}</p>
        <button className="btn btn--outline" onClick={() => window.location.reload()}>
          إعادة المحاولة
        </button>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="profile-page" dir="rtl">
      {/* ── Header Card ── */}
      <section className="profile-card">
        {/* Avatar */}
        <div className="profile-card__avatar-wrapper">
          {profile.avatarUrl ? (
            <img src={profile.avatarUrl} alt={profile.name} className="profile-card__avatar" />
          ) : (
            <div className="profile-card__avatar profile-card__avatar--initials">
              {getInitials(profile.name)}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="profile-card__info">
          <div className="profile-card__name-row">
            <h1 className="profile-card__name">{profile.name}</h1>
            <button
              className="btn btn--primary btn--sm"
              onClick={() => setEditOpen(true)}
            >
              <EditIcon />
              تعديل البروفايل
            </button>
          </div>

          {profile.jobTitle && (
            <p className="profile-card__job-title">{profile.jobTitle}</p>
          )}

          <p className="profile-card__email">{profile.email}</p>

          <div className="profile-card__meta">
            {profile.location && (
              <span className="profile-card__meta-item">
                <LocationIcon />
                {profile.location}
              </span>
            )}
            {profile.phone && (
              <span className="profile-card__meta-item">
                <PhoneIcon />
                {profile.phone}
              </span>
            )}
            {profile.linkedIn && (
              <a
                href={profile.linkedIn}
                target="_blank"
                rel="noreferrer"
                className="profile-card__meta-item profile-card__meta-link"
              >
                <LinkIcon />
                LinkedIn
              </a>
            )}
            {profile.portfolio && (
              <a
                href={profile.portfolio}
                target="_blank"
                rel="noreferrer"
                className="profile-card__meta-item profile-card__meta-link"
              >
                <LinkIcon />
                Portfolio
              </a>
            )}
          </div>
        </div>
      </section>

      {/* ── Bio ── */}
      {profile.bio && (
        <section className="profile-section">
          <h2 className="profile-section__title">نبذة شخصية</h2>
          <p className="profile-section__text">{profile.bio}</p>
        </section>
      )}

      {/* ── Skills ── */}
      {profile.skills && profile.skills.length > 0 && (
        <section className="profile-section">
          <h2 className="profile-section__title">المهارات</h2>
          <div className="skill-tags">
            {profile.skills.map((skill, i) => (
              <span key={i} className="skill-tag skill-tag--readonly">
                {skill}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* ── Edit Modal ── */}
      {editOpen && (
        <EditModal
          data={profile}
          onClose={() => setEditOpen(false)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}