import React, { useState, useEffect } from 'react';
import { 
  searchFirstAidGuides, 
  getWoundTypes, 
  getFirstAidStatistics,
  createFirstAidGuide,
  updateFirstAidGuide,
  deleteFirstAidGuide
} from '../../services/FirstAidService';

export default function FirstAidManagement() {
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters
  const [woundTypes, setWoundTypes] = useState([]);
  const [selectedWoundType, setSelectedWoundType] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('');
  
  // Statistics
  const [stats, setStats] = useState({
    total_guides: 0,
    wound_types: 0,
    active_guides: 0
  });
  
  // Modal states
  const [showViewModal, setShowViewModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedGuide, setSelectedGuide] = useState(null);
  
  // Form data
  const [formData, setFormData] = useState({
    wound_type: 'abrasion',
    severity: 'mild',
    sub_type: '',
    title: '',
    description: '',
  steps: [''],
    dos: [''],
    donts: [''],
    supplies_needed: [''],
    estimated_healing_time: ''
  });

  // Fetch wound types
  const fetchWoundTypes = async () => {
    try {
      const response = await getWoundTypes();
      if (response.success && response.data) {
        setWoundTypes(response.data);
      }
    } catch (err) {
      console.error('Error fetching wound types:', err);
    }
  };

  // Fetch statistics
  const fetchStatistics = async () => {
    try {
      const response = await getFirstAidStatistics();
      if (response.success && response.data) {
        // Map backend response to frontend expected format
        const statsData = response.data;
        setStats({
          total_guides: statsData.total_guides || 0,
          active_guides: statsData.total_guides || 0, // Backend doesn't separate active/inactive
          wound_types: statsData.wound_type_breakdown ? Object.keys(statsData.wound_type_breakdown).length : 0
        });
      }
    } catch (err) {
      console.error('Error fetching statistics:', err);
    }
  };

  // Fetch first aid guides
  const fetchGuides = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await searchFirstAidGuides({
        wound_type: selectedWoundType,
        severity: selectedSeverity,
        limit: 20,
        offset: 0
      });
      
      if (response.success && response.data) {
        setGuides(response.data);
      }
    } catch (err) {
      console.error('Error fetching guides:', err);
      setError(err.response?.data?.error || 'Failed to fetch first aid guides');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWoundTypes();
    fetchStatistics();
  }, []);

  useEffect(() => {
    fetchGuides();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWoundType, selectedSeverity]);

  // Handle wound type filter
  const handleWoundTypeChange = (e) => {
    setSelectedWoundType(e.target.value);
  };

  // Handle severity filter
  const handleSeverityChange = (e) => {
    setSelectedSeverity(e.target.value);
  };

  // Handle view guide
  const handleViewGuide = (guide) => {
    setSelectedGuide(guide);
    setShowViewModal(true);
  };

  // Handle close modal
  const handleCloseModal = () => {
    setShowViewModal(false);
    setSelectedGuide(null);
  };

  // Handle open add modal
  const handleOpenAddModal = () => {
    resetForm();
    setShowAddModal(true);
  };

  // Handle open edit modal
  const handleOpenEditModal = (guide) => {
    setSelectedGuide(guide);
    setFormData({
      wound_type: guide.wound_type,
      severity: guide.severity,
      sub_type: guide.sub_type || '',
      title: guide.title,
      description: guide.description || '',
  steps: guide.steps || [''],
      dos: guide.dos || [''],
      donts: guide.donts || [''],
      supplies_needed: guide.supplies_needed || [''],
      estimated_healing_time: guide.estimated_healing_time || ''
    });
    setShowEditModal(true);
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      wound_type: 'abrasion',
      severity: 'mild',
      sub_type: '',
      title: '',
      description: '',
  steps: [''],
      dos: [''],
      donts: [''],
      supplies_needed: [''],
      estimated_healing_time: ''
    });
  };

  // Handle form input change
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => {
      const updates = { [name]: value };
      
      // Reset sub_type when wound_type changes to non-burn
      if (name === 'wound_type' && value !== 'burn') {
        updates.sub_type = '';
      }
      
      return { ...prev, ...updates };
    });
  };

  // Handle array field change
  const handleArrayChange = (field, index, value) => {
    setFormData(prev => {
      const newArray = [...prev[field]];
      newArray[index] = value;
      return { ...prev, [field]: newArray };
    });
  };

  // Add array item
  const addArrayItem = (field) => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  // Remove array item
  const removeArrayItem = (field, index) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  // Handle add guide
  const handleAddGuide = async (e) => {
    e.preventDefault();
    try {
      // Filter out empty strings from arrays
  const cleanedSteps = formData.steps.filter(s => s && s.trim());
      const cleanedDos = formData.dos.filter(s => s && s.trim());
      const cleanedDonts = formData.donts.filter(s => s && s.trim());
      const cleanedSupplies = formData.supplies_needed.filter(s => s && s.trim());

      // Validate required fields
      if (!formData.title || !formData.title.trim()) {
        alert('Please provide a title for the guidance');
        return;
      }

      if (formData.title.trim().length < 5) {
        alert('Title must be at least 5 characters long');
        return;
      }

      if (cleanedSteps.length === 0) {
        alert('Please provide at least one step in the instructions');
        return;
      }

      // Build cleaned data object
      const cleanedData = {
        wound_type: formData.wound_type,
        severity: formData.severity,
        title: formData.title.trim(),
        steps: cleanedSteps
      };

      // Only add sub_type for burn wounds
      if (formData.wound_type === 'burn' && formData.sub_type) {
        cleanedData.sub_type = formData.sub_type;
      }

      // Add optional fields only if they have values
      if (formData.description && formData.description.trim()) {
        cleanedData.description = formData.description.trim();
      }
      
      if (formData.estimated_healing_time && formData.estimated_healing_time.trim()) {
        cleanedData.estimated_healing_time = formData.estimated_healing_time.trim();
      }
      
      if (cleanedDos.length > 0) {
        cleanedData.dos = cleanedDos;
      }
      
      if (cleanedDonts.length > 0) {
        cleanedData.donts = cleanedDonts;
      }
      
      if (cleanedSupplies.length > 0) {
        cleanedData.supplies_needed = cleanedSupplies;
      }

      console.log('Sending first aid guide data:', cleanedData);
      const response = await createFirstAidGuide(cleanedData);
      if (response.success) {
        setShowAddModal(false);
        resetForm();
        fetchGuides();
        fetchStatistics();
        alert('First aid guide created successfully!');
      } else {
        // Handle error response from server
        const errorMsg = response.message || response.error || 'Failed to create guide';
        const errorDetails = response.error_details ? 
          '\n\nDetails: ' + JSON.stringify(response.error_details, null, 2) : '';
        alert(errorMsg + errorDetails);
      }
    } catch (err) {
      console.error('Error creating guide:', err);
      
      // Extract error message from different possible structures
      let errorMessage = 'Failed to create guide';
      
      if (err.response?.data) {
        const errorData = err.response.data;
        errorMessage = errorData.message || errorData.error || errorData.detail;
        
        // If there's validation detail from FastAPI
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const validationErrors = errorData.detail.map(e => 
            `- ${e.loc.join('.')}: ${e.msg}`
          ).join('\n');
          errorMessage = 'Validation errors:\n' + validationErrors;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      alert(errorMessage);
    }
  };

  // Handle edit guide
  const handleEditGuide = async (e) => {
    e.preventDefault();
    try {
      // Filter out empty strings from arrays
      const cleanedData = {
        title: formData.title,
        description: formData.description || null,
        steps: formData.steps.filter(s => s.trim()),
        dos: formData.dos.filter(s => s.trim()),
        donts: formData.donts.filter(s => s.trim()),
        supplies_needed: formData.supplies_needed.filter(s => s.trim()),
        estimated_healing_time: formData.estimated_healing_time || null
      };

      // Remove empty arrays
      if (cleanedData.dos.length === 0) cleanedData.dos = null;
      if (cleanedData.donts.length === 0) cleanedData.donts = null;
      if (cleanedData.supplies_needed.length === 0) cleanedData.supplies_needed = null;

      const response = await updateFirstAidGuide(selectedGuide.firstaidguide_id, cleanedData);
      if (response.success) {
        setShowEditModal(false);
        resetForm();
        fetchGuides();
        alert('First aid guide updated successfully!');
      }
    } catch (err) {
      console.error('Error updating guide:', err);
      alert(err.response?.data?.error || 'Failed to update guide');
    }
  };

  // Handle delete guide
  const handleDeleteGuide = async (guideId, guideName) => {
    if (!window.confirm(`Are you sure you want to delete "${guideName}"?`)) {
      return;
    }

    try {
      const response = await deleteFirstAidGuide(guideId, false); // Soft delete
      if (response.success) {
        fetchGuides();
        fetchStatistics();
        alert('First aid guide deleted successfully!');
      }
    } catch (err) {
      console.error('Error deleting guide:', err);
      alert(err.response?.data?.error || 'Failed to delete guide');
    }
  };

  // Get severity badge class
  const getSeverityBadgeClass = (severity) => {
    switch (severity.toLowerCase()) {
      case 'mild':
        return 'badge badge-success';
      case 'moderate':
        return 'badge badge-warning';
      case 'severe':
        return 'badge badge-danger';
      default:
        return 'badge badge-default';
    }
  };

  // Format wound type display
  const formatWoundType = (woundType) => {
    const typeMap = {
      'abrasion': 'Scratch / Abrasion',
      'bruise': 'Bruise / Contusion',
      'burn': 'Burn',
      'cut': 'Cut / Laceration'
    };
    return typeMap[woundType.toLowerCase()] || woundType;
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="firstaid-management-page">
      {/* Page Header */}
      <div className="admin-page-header">
        <div className="admin-page-title">
          <h1>First Aid Guidance Management</h1>
          <p>Manage wound care and first aid content</p>
        </div>
        <button className="admin-btn-primary" onClick={handleOpenAddModal}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Add New Guidance
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon stat-icon-primary">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
          </div>
          <div className="stat-details">
            <div className="stat-value">{stats.total_guides}</div>
            <div className="stat-label">Total Guides</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon stat-icon-success">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <div className="stat-details">
            <div className="stat-value">{stats.active_guides}</div>
            <div className="stat-label">Active Guides</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon stat-icon-info">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
          </div>
          <div className="stat-details">
            <div className="stat-value">{stats.wound_types}</div>
            <div className="stat-label">Wound Types</div>
          </div>
        </div>
      </div>

      {/* Filters Section */}
      <div className="filters-section">
        <div className="filter-group">
          <label htmlFor="woundType">Wound Type</label>
          <select 
            id="woundType"
            value={selectedWoundType} 
            onChange={handleWoundTypeChange}
          >
            <option value="">All Types</option>
            {woundTypes.map((type) => (
              <option key={type.wound_type} value={type.wound_type}>
                {formatWoundType(type.wound_type)}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="severity">Severity</label>
          <select 
            id="severity"
            value={selectedSeverity} 
            onChange={handleSeverityChange}
          >
            <option value="">All Severities</option>
            <option value="mild">Mild</option>
            <option value="moderate">Moderate</option>
            <option value="severe">Severe</option>
          </select>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading first aid guides...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button onClick={fetchGuides} className="btn-retry">Retry</button>
        </div>
      )}

      {/* Guides Grid */}
      {!loading && !error && (
        <div className="guides-grid">
          {guides.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <p>No first aid guides found</p>
              <p className="empty-subtitle">Try adjusting your filters</p>
            </div>
          ) : (
            guides.map((guide) => (
              <div key={guide.firstaidguide_id} className="guide-card">
                <div className="guide-card-header">
                  <div className="guide-info">
                    <h3>{guide.title}</h3>
                    <div className="guide-meta">
                      <span className={getSeverityBadgeClass(guide.severity)}>
                        {guide.severity_display}
                      </span>
                      <span className="guide-date">
                        Updated: {formatDate(guide.updated_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="guide-card-body">
                  {guide.description && (
                    <p className="guide-description">{guide.description}</p>
                  )}
                  
                  <div className="guide-steps-preview">
                    <p className="steps-title">First Aid Steps:</p>
                    <ol className="steps-list">
                      {guide.steps && guide.steps.slice(0, 3).map((step, index) => (
                        <li key={index}>
                          <span className="step-number">{index + 1}</span>
                          <span className="step-text">{step}</span>
                        </li>
                      ))}
                    </ol>
                    {guide.steps && guide.steps.length > 3 && (
                      <p className="steps-more">+{guide.steps.length - 3} more steps</p>
                    )}
                  </div>

                  <div className="guide-card-actions">
                    <button 
                      className="btn-view-full"
                      onClick={() => handleViewGuide(guide)}
                    >
                      View Details
                    </button>
                    <button 
                      className="btn-edit"
                      onClick={() => handleOpenEditModal(guide)}
                      title="Edit"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                    </button>
                    <button 
                      className="btn-delete"
                      onClick={() => handleDeleteGuide(guide.firstaidguide_id, guide.title)}
                      title="Delete"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Medical Disclaimer */}
      <div className="disclaimer-card">
        <div className="disclaimer-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <div className="disclaimer-content">
          <p className="disclaimer-title">Medical Disclaimer</p>
          <p className="disclaimer-text">
            All first aid guidance should be reviewed and approved by qualified medical professionals. 
            This information is for educational purposes and should not replace professional medical advice. 
            Always consult with healthcare providers for serious injuries.
          </p>
        </div>
      </div>

      {/* View Modal */}
      {showViewModal && selectedGuide && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedGuide.title}</h2>
              <button className="modal-close" onClick={handleCloseModal}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <div className="modal-body">
              <div className="modal-info-grid">
                <div className="info-item">
                  <label>Wound Type</label>
                  <p>{formatWoundType(selectedGuide.wound_type)}</p>
                </div>
                <div className="info-item">
                  <label>Severity</label>
                  <span className={getSeverityBadgeClass(selectedGuide.severity)}>
                    {selectedGuide.severity_display}
                  </span>
                </div>
                {selectedGuide.sub_type && (
                  <div className="info-item">
                    <label>Sub Type</label>
                    <p>{selectedGuide.sub_type}</p>
                  </div>
                )}
                {selectedGuide.estimated_healing_time && (
                  <div className="info-item">
                    <label>Healing Time</label>
                    <p>{selectedGuide.estimated_healing_time}</p>
                  </div>
                )}
              </div>

              {selectedGuide.description && (
                <div className="modal-section">
                  <h3>Description</h3>
                  <p>{selectedGuide.description}</p>
                </div>
              )}

              {selectedGuide.steps && selectedGuide.steps.length > 0 && (
                <div className="modal-section">
                  <h3>First Aid Steps</h3>
                  <ol className="steps-list-full">
                    {selectedGuide.steps.map((step, index) => (
                      <li key={index}>
                        <span className="step-number">{index + 1}</span>
                        <span className="step-text">{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {selectedGuide.supplies_needed && selectedGuide.supplies_needed.length > 0 && (
                <div className="modal-section">
                  <h3>Supplies Needed</h3>
                  <ul className="supplies-list">
                    {selectedGuide.supplies_needed.map((supply, index) => (
                      <li key={index}>{supply}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedGuide.dos && selectedGuide.dos.length > 0 && (
                <div className="modal-section modal-section-success">
                  <h3>✓ Do's</h3>
                  <ul className="tips-list">
                    {selectedGuide.dos.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedGuide.donts && selectedGuide.donts.length > 0 && (
                <div className="modal-section modal-section-danger">
                  <h3>✗ Don'ts</h3>
                  <ul className="tips-list">
                    {selectedGuide.donts.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="modal-footer-info">
                <p><strong>Source:</strong> Based on WHO and Red Cross guidelines</p>
                <p><strong>Version:</strong> {selectedGuide.version}</p>
                <p><strong>Last Updated:</strong> {formatDate(selectedGuide.updated_at)}</p>
              </div>
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={handleCloseModal}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add New First Aid Guidance</h2>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <form onSubmit={handleAddGuide}>
              <div className="modal-body">
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="wound_type">Wound Type *</label>
                    <select
                      id="wound_type"
                      name="wound_type"
                      value={formData.wound_type}
                      onChange={handleInputChange}
                      required
                    >
                      <option value="abrasion">Scratch / Abrasion</option>
                      <option value="bruise">Bruise / Contusion</option>
                      <option value="burn">Burn</option>
                      <option value="cut">Cut / Laceration</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="severity">Severity *</label>
                    <select
                      id="severity"
                      name="severity"
                      value={formData.severity}
                      onChange={handleInputChange}
                      required
                    >
                      <option value="mild">Mild</option>
                      <option value="moderate">Moderate</option>
                      <option value="severe">Severe</option>
                    </select>
                  </div>

                  {formData.wound_type === 'burn' && (
                    <div className="form-group">
                      <label htmlFor="sub_type">Sub Type</label>
                      <select
                        id="sub_type"
                        name="sub_type"
                        value={formData.sub_type}
                        onChange={handleInputChange}
                      >
                        <option value="">None</option>
                        <option value="blister">Blister</option>
                        <option value="skintear">Skin Tear</option>
                      </select>
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="title">Title *</label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    required
                    placeholder="e.g., First Aid for Minor Burns"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="description">Description</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    rows="3"
                    placeholder="Brief description of the condition"
                  />
                </div>

                <div className="form-group">
                  <label>Steps * (at least 1)</label>
                  {formData.steps.map((step, index) => (
                    <div key={index} className="array-input-row">
                      <span className="array-index">{index + 1}</span>
                      <input
                        type="text"
                        value={step}
                        onChange={(e) => handleArrayChange('steps', index, e.target.value)}
                        placeholder="Enter step description"
                        required={index === 0}
                      />
                      {index > 0 && (
                        <button
                          type="button"
                          className="btn-remove-item"
                          onClick={() => removeArrayItem('steps', index)}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                  <button type="button" className="btn-add-item" onClick={() => addArrayItem('steps')}>
                    + Add Step
                  </button>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Do's (Recommended)</label>
                    {formData.dos.map((item, index) => (
                      <div key={index} className="array-input-row">
                        <input
                          type="text"
                          value={item}
                          onChange={(e) => handleArrayChange('dos', index, e.target.value)}
                          placeholder="What to do"
                        />
                        {formData.dos.length > 1 && (
                          <button
                            type="button"
                            className="btn-remove-item"
                            onClick={() => removeArrayItem('dos', index)}
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                    <button type="button" className="btn-add-item" onClick={() => addArrayItem('dos')}>
                      + Add Do
                    </button>
                  </div>

                  <div className="form-group">
                    <label>Don'ts (Avoid)</label>
                    {formData.donts.map((item, index) => (
                      <div key={index} className="array-input-row">
                        <input
                          type="text"
                          value={item}
                          onChange={(e) => handleArrayChange('donts', index, e.target.value)}
                          placeholder="What not to do"
                        />
                        {formData.donts.length > 1 && (
                          <button
                            type="button"
                            className="btn-remove-item"
                            onClick={() => removeArrayItem('donts', index)}
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                    <button type="button" className="btn-add-item" onClick={() => addArrayItem('donts')}>
                      + Add Don't
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label>Supplies Needed</label>
                  {formData.supplies_needed.map((supply, index) => (
                    <div key={index} className="array-input-row">
                      <input
                        type="text"
                        value={supply}
                        onChange={(e) => handleArrayChange('supplies_needed', index, e.target.value)}
                        placeholder="e.g., Sterile gauze, bandage"
                      />
                      {formData.supplies_needed.length > 1 && (
                        <button
                          type="button"
                          className="btn-remove-item"
                          onClick={() => removeArrayItem('supplies_needed', index)}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                  <button type="button" className="btn-add-item" onClick={() => addArrayItem('supplies_needed')}>
                    + Add Supply
                  </button>
                </div>

                <div className="form-group">
                  <label htmlFor="estimated_healing_time">Estimated Healing Time</label>
                  <input
                    type="text"
                    id="estimated_healing_time"
                    name="estimated_healing_time"
                    value={formData.estimated_healing_time}
                    onChange={handleInputChange}
                    placeholder="e.g., 1-2 weeks"
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  Create Guidance
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit First Aid Guidance</h2>
              <button className="modal-close" onClick={() => setShowEditModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <form onSubmit={handleEditGuide}>
              <div className="modal-body">
                <div className="form-alert">
                  <strong>Note:</strong> Wound type and severity cannot be changed. Create a new guidance instead.
                </div>

                <div className="form-group">
                  <label htmlFor="edit_title">Title *</label>
                  <input
                    type="text"
                    id="edit_title"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="edit_description">Description</label>
                  <textarea
                    id="edit_description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    rows="3"
                  />
                </div>

                <div className="form-group">
                  <label>Steps *</label>
                  {formData.steps.map((step, index) => (
                    <div key={index} className="array-input-row">
                      <span className="array-index">{index + 1}</span>
                      <input
                        type="text"
                        value={step}
                        onChange={(e) => handleArrayChange('steps', index, e.target.value)}
                        required={index === 0}
                      />
                      {index > 0 && (
                        <button
                          type="button"
                          className="btn-remove-item"
                          onClick={() => removeArrayItem('steps', index)}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                  <button type="button" className="btn-add-item" onClick={() => addArrayItem('steps')}>
                    + Add Step
                  </button>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Do's</label>
                    {formData.dos.map((item, index) => (
                      <div key={index} className="array-input-row">
                        <input
                          type="text"
                          value={item}
                          onChange={(e) => handleArrayChange('dos', index, e.target.value)}
                        />
                        {formData.dos.length > 1 && (
                          <button
                            type="button"
                            className="btn-remove-item"
                            onClick={() => removeArrayItem('dos', index)}
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                    <button type="button" className="btn-add-item" onClick={() => addArrayItem('dos')}>
                      + Add Do
                    </button>
                  </div>

                  <div className="form-group">
                    <label>Don'ts</label>
                    {formData.donts.map((item, index) => (
                      <div key={index} className="array-input-row">
                        <input
                          type="text"
                          value={item}
                          onChange={(e) => handleArrayChange('donts', index, e.target.value)}
                        />
                        {formData.donts.length > 1 && (
                          <button
                            type="button"
                            className="btn-remove-item"
                            onClick={() => removeArrayItem('donts', index)}
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                    <button type="button" className="btn-add-item" onClick={() => addArrayItem('donts')}>
                      + Add Don't
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label>Supplies Needed</label>
                  {formData.supplies_needed.map((supply, index) => (
                    <div key={index} className="array-input-row">
                      <input
                        type="text"
                        value={supply}
                        onChange={(e) => handleArrayChange('supplies_needed', index, e.target.value)}
                      />
                      {formData.supplies_needed.length > 1 && (
                        <button
                          type="button"
                          className="btn-remove-item"
                          onClick={() => removeArrayItem('supplies_needed', index)}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                  <button type="button" className="btn-add-item" onClick={() => addArrayItem('supplies_needed')}>
                    + Add Supply
                  </button>
                </div>

                <div className="form-group">
                  <label htmlFor="edit_estimated_healing_time">Estimated Healing Time</label>
                  <input
                    type="text"
                    id="edit_estimated_healing_time"
                    name="estimated_healing_time"
                    value={formData.estimated_healing_time}
                    onChange={handleInputChange}
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  Save Changes
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowEditModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
