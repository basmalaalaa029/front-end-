import React, { forwardRef } from 'react';
import type { CVData } from '../types';
import { MapPin, Mail, Phone } from 'lucide-react';
import { FaGithub, FaLinkedin } from 'react-icons/fa';

interface Props {
  data: CVData;
}

export const CVPreview = forwardRef<HTMLDivElement, Props>(({ data }, ref) => {
  const { personalInfo, experiences, education, skills, languages } = data;

  return (
    <div 
      ref={ref} 
      className="bg-white text-gray-900 w-full min-h-[1056px] shadow-sm font-sans p-10 mx-auto"
      style={{ width: '210mm', minHeight: '297mm' }}
      dir="ltr"
    >
      {/* Header - Personal Info */}
      <div className="border-b-2 border-gray-900 pb-6 mb-6">
        <h1 className="text-4xl font-black text-gray-900 mb-2 uppercase tracking-wide">
          {personalInfo.name || "YOUR NAME"}
        </h1>
        
        <div className="flex flex-wrap gap-4 text-sm text-gray-600 mt-3">
          {personalInfo.email && (
            <div className="flex items-center gap-1.5">
              <Mail size={14} /> {personalInfo.email}
            </div>
          )}
          {personalInfo.phone && (
            <div className="flex items-center gap-1.5">
              <Phone size={14} /> {personalInfo.phone}
            </div>
          )}
          {personalInfo.address && (
            <div className="flex items-center gap-1.5">
              <MapPin size={14} /> {personalInfo.address}
            </div>
          )}
          {personalInfo.linkedin && (
            <div className="flex items-center gap-1.5">
              <FaLinkedin size={14} /> {personalInfo.linkedin}
            </div>
          )}
          {personalInfo.github && (
            <div className="flex items-center gap-1.5">
                <FaGithub size={14} /> {personalInfo.github}
            </div>
          )}
        </div>

        {personalInfo.summary && (
          <p className="mt-4 text-sm text-gray-700 leading-relaxed text-justify">
            {personalInfo.summary}
          </p>
        )}
      </div>

      <div className="grid grid-cols-3 gap-8">
        {/* Main Column */}
        <div className="col-span-2 space-y-8">
          {/* Experience */}
          {experiences.length > 0 && experiences.some(e => e.company || e.role) && (
            <section>
              <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wider border-b border-gray-300 pb-1 mb-4">
                Experience
              </h2>
              <div className="space-y-5">
                {experiences.map((exp, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between items-baseline mb-1">
                      <h3 className="font-bold text-gray-800">{exp.role || "Job Title"}</h3>
                      <span className="text-sm font-medium text-gray-500">{exp.duration || "Date"}</span>
                    </div>
                    <div className="text-sm font-semibold text-blue-600 mb-2">{exp.company || "Company Name"}</div>
                    <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                      {exp.description || "Description of your responsibilities and achievements."}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Education */}
          {education.length > 0 && education.some(e => e.institution || e.degree) && (
            <section>
              <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wider border-b border-gray-300 pb-1 mb-4">
                Education
              </h2>
              <div className="space-y-4">
                {education.map((edu, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between items-baseline mb-1">
                      <h3 className="font-bold text-gray-800">{edu.degree || "Degree"}</h3>
                      <span className="text-sm font-medium text-gray-500">{edu.year || "Year"}</span>
                    </div>
                    <div className="text-sm text-gray-600">{edu.institution || "Institution Name"}</div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar */}
        <div className="col-span-1 space-y-8">
          {/* Skills */}
          {skills.length > 0 && skills.some(s => s.name) && (
            <section>
              <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wider border-b border-gray-300 pb-1 mb-4">
                Skills
              </h2>
              <div className="flex flex-wrap gap-2">
                {skills.map((skill, idx) => (
                  skill.name ? (
                    <span key={idx} className="bg-gray-100 text-gray-800 text-xs font-semibold px-2.5 py-1 rounded">
                      {skill.name} {skill.level ? `• ${skill.level}` : ''}
                    </span>
                  ) : null
                ))}
              </div>
            </section>
          )}

          {/* Languages */}
          {languages.length > 0 && languages.some(l => l.name) && (
            <section>
              <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wider border-b border-gray-300 pb-1 mb-4">
                Languages
              </h2>
              <ul className="space-y-2">
                {languages.map((lang, idx) => (
                  lang.name ? (
                    <li key={idx} className="flex justify-between text-sm">
                      <span className="font-medium text-gray-800">{lang.name}</span>
                      <span className="text-gray-500">{lang.proficiency}</span>
                    </li>
                  ) : null
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  );
});

CVPreview.displayName = 'CVPreview';