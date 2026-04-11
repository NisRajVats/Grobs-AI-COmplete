/**
 * Normalize Resume Payload Utility
 * 
 * This function normalizes resume data from AI responses to match the backend Pydantic schema.
 * It handles inconsistent data formats and ensures all fields are properly structured.
 * 
 * Backend expects:
 * - skills: [{ name: string, category: string }]
 * - experience: [{ company, role, location, start_date, end_date, current, description }]
 * - education: [{ school, degree, major, gpa, start_date, end_date, year, description }]
 * - projects: [{ project_name, description, technologies (string), project_url, github_url, points }]
 */

/**
 * Normalizes skills data to always be an array of { name, category } objects
 * Handles: ["React", "Node"] AND [{name: "React"}] AND [{name: "React", category: "Frontend"}]
 * @param {any} skills - Skills data in various formats
 * @returns {Array<{name: string, category: string}>} Normalized skills array
 */
function normalizeSkills(skills) {
  // If null, undefined, or not an array, return empty array
  if (!skills || (!Array.isArray(skills) && typeof skills !== 'object')) {
    return [];
  }

  // If it's a plain string, try to parse as comma-separated
  if (typeof skills === 'string') {
    return skills
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
      .map((s) => ({ name: s, category: 'Technical' }));
  }

  // If it's an array, process each item
  if (Array.isArray(skills)) {
    return skills
      .filter((skill) => skill != null) // Remove null/undefined
      .map((skill) => {
        // If it's a string, convert to object
        if (typeof skill === 'string') {
          return { name: skill.trim(), category: 'Technical' };
        }
        // If it's an object, ensure it has name and category
        if (typeof skill === 'object' && skill !== null) {
          return {
            name: String(skill.name || skill.skill || skill.title || ''),
            category: String(skill.category || 'Technical'),
          };
        }
        return null;
      })
      .filter((skill) => skill && skill.name); // Remove invalid entries
  }

  return [];
}

/**
 * Normalizes experience data to always include required fields
 * Handles both 'description' and 'desc' field names
 * @param {any} experience - Experience data in various formats
 * @returns {Array} Normalized experience array
 */
function normalizeExperience(experience) {
  // If null, undefined, or not an array, return empty array
  if (!experience || !Array.isArray(experience)) {
    return [];
  }

  return experience
    .filter((exp) => exp != null && typeof exp === 'object')
    .map((exp) => ({
      company: String(exp.company || exp.company_name || exp.organization || ''),
      role: String(exp.role || exp.position || exp.title || exp.job_title || ''),
      location: String(exp.location || exp.city || exp.place || ''),
      start_date: String(exp.start_date || exp.start || exp.startDate || ''),
      end_date: String(exp.end_date || exp.end || exp.endDate || ''),
      current: Boolean(exp.current || exp.is_current || exp.present || false),
      description: String(exp.description || exp.desc || exp.details || exp.summary || ''),
    }))
    .filter((exp) => exp.company || exp.role); // Keep only entries with at least company or role
}

/**
 * Normalizes education data to always include required fields
 * Avoids undefined values by providing defaults
 * @param {any} education - Education data in various formats
 * @returns {Array} Normalized education array
 */
function normalizeEducation(education) {
  // If null, undefined, or not an array, return empty array
  if (!education || !Array.isArray(education)) {
    return [];
  }

  return education
    .filter((edu) => edu != null && typeof edu === 'object')
    .map((edu) => ({
      school: String(edu.school || edu.institution || edu.university || edu.college || edu.name || ''),
      degree: String(edu.degree || edu.qualification || ''),
      major: String(edu.major || edu.field_of_study || edu.field || edu.specialization || ''),
      gpa: edu.gpa != null ? String(edu.gpa) : '',
      start_date: String(edu.start_date || edu.start || edu.startDate || ''),
      end_date: String(edu.end_date || edu.end || edu.endDate || edu.year || ''),
      year: edu.year != null ? String(edu.year) : '',
      description: String(edu.description || edu.desc || edu.details || ''),
    }))
    .filter((edu) => edu.school); // Keep only entries with at least school name
}

/**
 * Normalizes projects data to always include required fields
 * Converts technologies to string ALWAYS - handles string, array, or invalid types safely
 * @param {any} projects - Projects data in various formats
 * @returns {Array} Normalized projects array
 */
function normalizeProjects(projects) {
  // If null, undefined, or not an array, return empty array
  if (!projects || !Array.isArray(projects)) {
    return [];
  }

  return projects
    .filter((proj) => proj != null && typeof proj === 'object')
    .map((proj) => {
      // Normalize technologies to string
      let technologies = '';
      if (proj.technologies != null) {
        if (typeof proj.technologies === 'string') {
          technologies = proj.technologies;
        } else if (Array.isArray(proj.technologies)) {
          technologies = proj.technologies
            .filter((t) => t != null)
            .map((t) => String(t))
            .join(', ');
        } else if (typeof proj.technologies === 'object') {
          // Handle case where technologies might be a dict/object
          technologies = String(proj.technologies);
        } else {
          technologies = String(proj.technologies);
        }
      }

      return {
        project_name: String(proj.project_name || proj.name || proj.title || proj.project || ''),
        description: String(proj.description || proj.desc || proj.details || proj.summary || ''),
        technologies: technologies,
        project_url: String(proj.project_url || proj.url || proj.link || proj.website || ''),
        github_url: String(proj.github_url || proj.github || proj.repo || ''),
        points: Array.isArray(proj.points)
          ? proj.points.filter((p) => typeof p === 'string').map((p) => p.trim())
          : [],
      };
    })
    .filter((proj) => proj.project_name); // Keep only entries with at least project name
}

/**
 * Main function to normalize the entire resume payload
 * Removes undefined/null fields to prevent overwriting existing DB data
 * Only includes valid fields that match the backend schema exactly
 * 
 * @param {Object} data - Raw resume data from AI response
 * @returns {Object} Normalized payload ready for backend API
 */
export function normalizeResumePayload(data) {
  // If data is null/undefined, return empty object
  if (!data || typeof data !== 'object') {
    console.debug('[normalizeResumePayload] Invalid input, returning empty payload');
    return {};
  }

  const normalized = {};

  // Handle string fields - only include if they have meaningful content
  if (data.summary && typeof data.summary === 'string' && data.summary.trim()) {
    normalized.summary = data.summary.trim();
  }

  if (data.full_name && typeof data.full_name === 'string' && data.full_name.trim()) {
    normalized.full_name = data.full_name.trim();
  }

  if (data.email && typeof data.email === 'string' && data.email.trim()) {
    normalized.email = data.email.trim();
  }

  if (data.phone && typeof data.phone === 'string' && data.phone.trim()) {
    normalized.phone = data.phone.trim();
  }

  if (data.linkedin_url && typeof data.linkedin_url === 'string' && data.linkedin_url.trim()) {
    normalized.linkedin_url = data.linkedin_url.trim();
  }

  if (data.title && typeof data.title === 'string' && data.title.trim()) {
    normalized.title = data.title.trim();
  }

  if (data.target_role && typeof data.target_role === 'string' && data.target_role.trim()) {
    normalized.target_role = data.target_role.trim();
  }

  // Normalize complex fields with safety checks
  // Use empty array as default if the field doesn't exist or is invalid
  const skillsData = data.skills || [];
  normalized.skills = normalizeSkills(skillsData);
  console.debug('[normalizeResumePayload] Normalized skills:', normalized.skills);

  const experienceData = data.experience || [];
  normalized.experience = normalizeExperience(experienceData);
  console.debug('[normalizeResumePayload] Normalized experience:', normalized.experience);

  const educationData = data.education || [];
  normalized.education = normalizeEducation(educationData);
  console.debug('[normalizeResumePayload] Normalized education:', normalized.education);

  const projectsData = data.projects || [];
  normalized.projects = normalizeProjects(projectsData);
  console.debug('[normalizeResumePayload] Normalized projects:', normalized.projects);

  console.debug('[normalizeResumePayload] Final normalized payload:', normalized);

  return normalized;
}

// Export individual normalizers for testing or standalone use
export { normalizeSkills, normalizeExperience, normalizeEducation, normalizeProjects };

export default normalizeResumePayload;