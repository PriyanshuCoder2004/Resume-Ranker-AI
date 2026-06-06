document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const form = document.getElementById('screeningForm');
    const jdInput = document.getElementById('jd');
    const loadSampleBtn = document.getElementById('loadSampleJd');
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('resumes');
    const fileListContainer = document.getElementById('fileList');
    
    // States
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const resultsDashboard = document.getElementById('resultsDashboard');
    
    // Stats & Output
    const statTotal = document.getElementById('statTotal');
    const statTopScore = document.getElementById('statTopScore');
    const rankingsTableBody = document.getElementById('rankingsTableBody');
    
    // Modal
    const detailsModal = document.getElementById('detailsModal');
    const closeModalBtn = document.getElementById('closeModal');
    const modalCandidateName = document.getElementById('modalCandidateName');
    const modalSimilarityScore = document.getElementById('modalSimilarityScore');
    const modalSkillScore = document.getElementById('modalSkillScore');
    const matchedCount = document.getElementById('matchedCount');
    const missingCount = document.getElementById('missingCount');
    const matchedSkillsList = document.getElementById('matchedSkillsList');
    const missingSkillsList = document.getElementById('missingSkillsList');

    // Global variables to store session data
    let uploadedFilesList = [];
    let responseData = null;

    // Sample Job Description template
    const SAMPLE_JD = `Job Title: Senior Backend & DevOps Engineer

Role Overview:
We are seeking a senior software engineer to lead the design and implementation of backend systems and deployment pipelines. You will write high-quality services, integrate databases, containerize services, and deploy applications to cloud infrastructures.

Responsibilities:
- Write backend code, design APIs, and build services using Python.
- Deploy robust database systems using SQL and PostgreSQL.
- Containerize components with Docker and manage orchestrations in Kubernetes.
- Configure cloud infrastructures on AWS.
- Use Git and DevOps practices to maintain continuous integration.

Technical Skills Required:
Python, SQL, PostgreSQL, AWS, Docker, Kubernetes, Git, DevOps.`;

    // Load Sample JD text
    loadSampleBtn.addEventListener('click', () => {
        jdInput.value = SAMPLE_JD;
        // Scroll to text area smoothly
        jdInput.scrollIntoView({ behavior: 'smooth' });
    });

    // ==========================================================================
    // FILE DRAG & DROP HANDLERS
    // ==========================================================================
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Validate PDF extension
            if (file.type !== 'application/pdf' && !file.name.toLowerCase().endswith('.pdf')) {
                alert(`Error: "${file.name}" is not a PDF file. Only PDF resumes are accepted.`);
                continue;
            }
            
            // Prevent duplicate file selection
            if (uploadedFilesList.some(f => f.name === file.name && f.size === file.size)) {
                continue;
            }
            
            uploadedFilesList.push(file);
        }
        updateFileListView();
    }

    function updateFileListView() {
        fileListContainer.innerHTML = '';
        
        if (uploadedFilesList.length === 0) {
            fileInput.required = true;
            return;
        }
        
        fileInput.required = false; // Override since we track files in memory array
        
        uploadedFilesList.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const sizeInMb = (file.size / (1024 * 1024)).toFixed(2);
            
            fileItem.innerHTML = `
                <div class="file-item-info">
                    <i class="fa-solid fa-file-pdf"></i>
                    <span><strong>${file.name}</strong> (${sizeInMb} MB)</span>
                </div>
                <button type="button" class="file-item-remove" data-index="${index}">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            `;
            
            fileListContainer.appendChild(fileItem);
        });

        // Add event listeners to remove buttons
        document.querySelectorAll('.file-item-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.currentTarget.getAttribute('data-index'));
                uploadedFilesList.splice(idx, 1);
                updateFileListView();
            });
        });
    }

    // ==========================================================================
    // FORM SUBMISSION (RANK ENDPOINT INVOCATION)
    // ==========================================================================
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const jdValue = jdInput.value.trim();
        if (!jdValue) {
            alert('Please provide a Job Description.');
            return;
        }

        if (uploadedFilesList.length === 0) {
            alert('Please select or upload at least one PDF resume.');
            return;
        }

        // Show Loading UI, Hide Empty & Results UI
        emptyState.classList.add('hidden');
        resultsDashboard.classList.add('hidden');
        loadingState.classList.remove('hidden');
        
        // Disable Screen Button
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;

        const formData = new FormData();
        formData.append('jd', jdValue);
        
        // Append all selected files to request
        uploadedFilesList.forEach(file => {
            formData.append('resumes', file);
        });

        try {
            const response = await fetch('/rank', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Server returned an error.');
            }

            responseData = data;
            renderResults(data);
            
        } catch (error) {
            console.error('Error screening resumes:', error);
            alert(`Screening Failed:\n${error.message}`);
            // Restore UI back to empty
            emptyState.classList.remove('hidden');
            resultsDashboard.classList.add('hidden');
        } finally {
            // Restore loader & button
            loadingState.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });

    // ==========================================================================
    // RENDER SEARCH RESULTS
    // ==========================================================================
    function renderResults(data) {
        const rankings = data.results;
        const skills = data.skill_breakdown;

        statTotal.textContent = rankings.length;
        
        if (rankings.length > 0) {
            statTopScore.textContent = `${rankings[0].score}%`;
        } else {
            statTopScore.textContent = '0%';
        }

        rankingsTableBody.innerHTML = '';

        rankings.forEach(candidate => {
            const name = candidate.name;
            const rank = candidate.rank;
            const simScore = candidate.score;
            
            // Fetch matching skill info
            const skillInfo = skills[name] || { skill_score: 0.0 };
            const skillScore = skillInfo.skill_score;

            // Set Rank Badge Style
            let rankBadgeClass = 'rank-badge-default';
            if (rank === 1) rankBadgeClass = 'rank-badge-1';
            else if (rank === 2) rankBadgeClass = 'rank-badge-2';
            else if (rank === 3) rankBadgeClass = 'rank-badge-3';

            // Set Progress Bar color depends on score
            let fillClass = 'fill-low';
            if (simScore >= 60) fillClass = 'fill-high';
            else if (simScore >= 30) fillClass = 'fill-med';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><span class="rank-badge ${rankBadgeClass}">${rank}</span></td>
                <td><strong class="file-name">${name}</strong></td>
                <td>
                    <div class="score-progress-container">
                        <span class="score-num">${simScore}%</span>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill ${fillClass}" style="width: ${simScore}%"></div>
                        </div>
                    </div>
                </td>
                <td><span class="score-num">${skillScore}%</span></td>
                <td>
                    <button class="btn-secondary btn-sm view-details-btn" data-filename="${name}">
                        <i class="fa-solid fa-circle-info"></i> View Details
                    </button>
                </td>
            `;

            rankingsTableBody.appendChild(tr);
        });

        // Add details view event listeners
        document.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filename = e.currentTarget.getAttribute('data-filename');
                openDetailsModal(filename);
            });
        });

        // Show Dashboard Panel
        resultsDashboard.classList.remove('hidden');
    }

    // ==========================================================================
    // DETAIL MODAL OPERATORS
    // ==========================================================================
    function openDetailsModal(filename) {
        if (!responseData) return;

        const candidateRank = responseData.results.find(c => c.name === filename);
        const skillBreakdown = responseData.skill_breakdown[filename];

        if (!candidateRank || !skillBreakdown) return;

        modalCandidateName.textContent = filename;
        modalSimilarityScore.textContent = `${candidateRank.score}%`;
        modalSkillScore.textContent = `${skillBreakdown.skill_score}%`;

        // Clear Lists
        matchedSkillsList.innerHTML = '';
        missingSkillsList.innerHTML = '';

        // Render Matched
        const matched = skillBreakdown.found;
        matchedCount.textContent = matched.length;
        if (matched.length > 0) {
            matched.forEach(skill => {
                const badge = document.createElement('span');
                badge.className = 'skill-badge matched-badge';
                badge.textContent = skill;
                matchedSkillsList.appendChild(badge);
            });
        } else {
            matchedSkillsList.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">No matched skills.</span>';
        }

        // Render Missing
        const missing = skillBreakdown.missing;
        missingCount.textContent = missing.length;
        if (missing.length > 0) {
            missing.forEach(skill => {
                const badge = document.createElement('span');
                badge.className = 'skill-badge missing-badge';
                badge.textContent = skill;
                missingSkillsList.appendChild(badge);
            });
        } else {
            missingSkillsList.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">No missing skills! Excellent fit!</span>';
        }

        // Display Modal
        detailsModal.classList.remove('hidden');
    }

    closeModalBtn.addEventListener('click', () => {
        detailsModal.classList.add('hidden');
    });

    // Close modal if user clicks outside of modal container
    window.addEventListener('click', (e) => {
        if (e.target === detailsModal) {
            detailsModal.classList.add('hidden');
        }
    });
});
