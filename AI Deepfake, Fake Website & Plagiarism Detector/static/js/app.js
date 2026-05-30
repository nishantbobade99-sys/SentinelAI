document.addEventListener('DOMContentLoaded', () => {
    // --- State & Config ---
    let authToken = localStorage.getItem('sentinel_token');
    const API_BASE = '/api';

    // --- DOM Elements ---
    const authOverlay = document.getElementById('auth-overlay');
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    const logoutBtn = document.getElementById('logout-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const navBtns = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // --- Auth Logic ---
    function checkAuth() {
        if (authToken) {
            authOverlay.style.display = 'none';
            logoutBtn.style.display = 'block';
            fetchSystemStatus(); // Load status on auth
        } else {
            authOverlay.style.display = 'flex';
            logoutBtn.style.display = 'none';
        }
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            
            if (data.success) {
                authToken = data.token;
                localStorage.setItem('sentinel_token', authToken);
                loginError.textContent = '';
                checkAuth();
            } else {
                loginError.textContent = data.message || 'Login failed';
            }
        } catch (err) {
            loginError.textContent = 'Server error. Please try again.';
        }
    });

    logoutBtn.addEventListener('click', () => {
        authToken = null;
        localStorage.removeItem('sentinel_token');
        checkAuth();
    });

    // --- Navigation ---
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
            
            if(btn.dataset.target === 'system-status') {
                fetchSystemStatus();
            }
        });
    });

    // Inner Tabs
    document.querySelectorAll('.inner-tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const parent = e.target.closest('.main-panel');
            parent.querySelectorAll('.inner-tab').forEach(b => b.classList.remove('active'));
            parent.querySelectorAll('.inner-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
        });
    });

    // --- Helpers ---
    function showLoading(show) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    function renderError(container, message) {
        container.style.display = 'block';
        container.className = 'result-container error';
        container.innerHTML = `
            <div class="result-header">
                <h3>Analysis Failed</h3>
                <span class="verdict danger">ERROR</span>
            </div>
            <p>${message}</p>
        `;
    }

    async function apiCall(endpoint, options = {}) {
        options.headers = options.headers || {};
        if (authToken) {
            options.headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const res = await fetch(`${API_BASE}/${endpoint}`, options);
        const data = await res.json();
        
        if (res.status === 401) {
            logoutBtn.click(); // Auto logout on invalid token
            throw new Error('Unauthorized');
        }
        
        if (!res.ok) {
            throw new Error(data.message || 'API Error');
        }
        
        return data;
    }

    // --- Image Deepfake ---
    const imageInput = document.getElementById('image-input');
    const imageUploadArea = document.getElementById('image-upload-area');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const analyzeImageBtn = document.getElementById('analyze-image-btn');
    const imageResult = document.getElementById('image-result');
    let currentImageFile = null;

    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            currentImageFile = e.target.files[0];
            imagePreview.src = URL.createObjectURL(currentImageFile);
            imageUploadArea.style.display = 'none';
            imagePreviewContainer.style.display = 'block';
            imageResult.style.display = 'none';
        }
    });

    analyzeImageBtn.addEventListener('click', async () => {
        if (!currentImageFile) return;
        
        const formData = new FormData();
        formData.append('file', currentImageFile);
        
        showLoading(true);
        try {
            const data = await apiCall('detect/image', {
                method: 'POST',
                body: formData
            });
            
            if (data.success) {
                renderImageResult(data);
            } else {
                renderError(imageResult, data.message);
            }
        } catch (err) {
            renderError(imageResult, err.message);
        } finally {
            showLoading(false);
        }
    });

    function renderImageResult(data) {
        imageResult.style.display = 'block';
        imageResult.className = `result-container ${data.verdict === 'FAKE' ? 'error' : ''}`;
        
        imageResult.innerHTML = `
            <div class="result-header">
                <h3>Analysis Complete</h3>
                <span class="verdict ${data.verdict === 'FAKE' ? 'danger' : 'safe'}">${data.verdict}</span>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">Fake Probability</div>
                    <div class="metric-value">${(data.fake_probability * 100).toFixed(1)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Real Probability</div>
                    <div class="metric-value">${(data.real_probability * 100).toFixed(1)}%</div>
                </div>
            </div>
            <div class="evidence">
                <strong>Reasoning:</strong> ${data.evidence.reasoning}
            </div>
        `;
    }

    // --- Website Phishing ---
    const urlInput = document.getElementById('url-input');
    const analyzeUrlBtn = document.getElementById('analyze-url-btn');
    const websiteResult = document.getElementById('website-result');

    analyzeUrlBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) return;
        
        showLoading(true);
        try {
            const data = await apiCall('detect/website', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            
            if (data.success) {
                renderWebsiteResult(data);
            } else {
                renderError(websiteResult, data.message);
            }
        } catch (err) {
            renderError(websiteResult, err.message);
        } finally {
            showLoading(false);
        }
    });

    function renderWebsiteResult(data) {
        websiteResult.style.display = 'block';
        let cls = '';
        let vCls = 'safe';
        if (data.verdict === 'PHISHING') { cls = 'error'; vCls = 'danger'; }
        if (data.verdict === 'SUSPICIOUS') { cls = 'warning'; vCls = 'warning'; }
        
        websiteResult.className = `result-container ${cls}`;
        
        let evidenceStr = data.evidence ? data.evidence.reasoning : '';
        
        websiteResult.innerHTML = `
            <div class="result-header">
                <h3>URL Analysis ${data.mode === 'rule_based_fallback' ? '(Fallback Mode)' : ''}</h3>
                <span class="verdict ${vCls}">${data.verdict}</span>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">Phishing Probability</div>
                    <div class="metric-value">${(data.phishing_probability * 100).toFixed(1)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Safe Probability</div>
                    <div class="metric-value">${(data.safe_probability * 100).toFixed(1)}%</div>
                </div>
            </div>
            <div class="evidence">
                <strong>Indicators:</strong> ${evidenceStr}
            </div>
        `;
    }

    // --- Text / Document ---
    const textInput = document.getElementById('text-input');
    const analyzeTextBtn = document.getElementById('analyze-text-btn');
    const docInput = document.getElementById('doc-input');
    const docFileName = document.getElementById('doc-file-name');
    const analyzeDocBtn = document.getElementById('analyze-doc-btn');
    const textResult = document.getElementById('text-result');
    let currentDocFile = null;

    docInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            currentDocFile = e.target.files[0];
            docFileName.textContent = currentDocFile.name;
            analyzeDocBtn.style.display = 'block';
        }
    });

    analyzeTextBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (!text) return;
        
        showLoading(true);
        try {
            const data = await apiCall('detect/text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            renderTextResult(data);
        } catch (err) {
            renderError(textResult, err.message);
        } finally {
            showLoading(false);
        }
    });

    analyzeDocBtn.addEventListener('click', async () => {
        if (!currentDocFile) return;
        
        const formData = new FormData();
        formData.append('file', currentDocFile);
        
        showLoading(true);
        try {
            const data = await apiCall('detect/document', {
                method: 'POST',
                body: formData
            });
            renderTextResult(data);
        } catch (err) {
            renderError(textResult, err.message);
        } finally {
            showLoading(false);
        }
    });

    function renderTextResult(data) {
        textResult.style.display = 'block';
        textResult.className = `result-container`;
        
        const plag = data.plagiarism_result || {};
        const ai = data.ai_generated_result || {};
        
        let plagHtml = '';
        if (plag.success === false) {
            plagHtml = `<p class="error-msg">${plag.message}</p>`;
        } else if (plag.status === 'NO_CORPUS') {
            plagHtml = `<p class="error-msg">${plag.message}</p>`;
        } else {
            let pCls = plag.verdict === 'ORIGINAL' ? 'safe' : (plag.verdict === 'PLAGIARIZED' ? 'danger' : 'warning');
            plagHtml = `
                <div style="margin-bottom: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem;">
                    <div class="result-header">
                        <h4>Plagiarism Check</h4>
                        <span class="verdict ${pCls}">${plag.verdict}</span>
                    </div>
                    <p>Similarity Score: ${(plag.similarity_score * 100).toFixed(1)}%</p>
                    ${plag.matched_source ? `<p><small>Matched Source: ${plag.matched_source}</small></p>` : ''}
                </div>
            `;
        }
        
        let aiHtml = '';
        if (ai.available === false) {
            aiHtml = `<p class="error-msg">${ai.message}</p>`;
        } else {
            let aCls = ai.verdict === 'HUMAN_WRITTEN' ? 'safe' : (ai.verdict === 'AI_GENERATED' ? 'danger' : 'warning');
            aiHtml = `
                <div>
                    <div class="result-header">
                        <h4>AI Text Detection</h4>
                        <span class="verdict ${aCls}">${ai.verdict}</span>
                    </div>
                    <div class="metrics-grid" style="margin-top: 1rem;">
                        <div class="metric-card">
                            <div class="metric-title">AI Probability</div>
                            <div class="metric-value">${(ai.ai_probability * 100).toFixed(1)}%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">Human Probability</div>
                            <div class="metric-value">${(ai.human_probability * 100).toFixed(1)}%</div>
                        </div>
                    </div>
                </div>
            `;
        }

        textResult.innerHTML = plagHtml + aiHtml;
    }

    // --- System Status ---
    const statusContainer = document.getElementById('status-container');
    const refreshStatusBtn = document.getElementById('refresh-status-btn');

    refreshStatusBtn.addEventListener('click', fetchSystemStatus);

    async function fetchSystemStatus() {
        if(!authToken) return;
        
        try {
            const data = await apiCall('model-status');
            if(data.success) {
                statusContainer.innerHTML = `
                    <div class="status-item">
                        <span>Image Deepfake Model</span>
                        <span class="status-indicator ${data.image_model}">${data.image_model.toUpperCase()}</span>
                    </div>
                    <div class="status-item">
                        <span>Website Phishing Model</span>
                        <span class="status-indicator ${data.website_model}">${data.website_model.toUpperCase()}</span>
                    </div>
                    <div class="status-item">
                        <span>Plagiarism Corpus</span>
                        <span class="status-indicator ${data.plagiarism_corpus}">${data.plagiarism_corpus.toUpperCase()}</span>
                    </div>
                    <div class="status-item">
                        <span>AI Text Classifier</span>
                        <span class="status-indicator ${data.ai_text_model}">${data.ai_text_model.toUpperCase()}</span>
                    </div>
                `;
            }
        } catch (err) {
            statusContainer.innerHTML = `<p class="error-msg">Failed to load system status: ${err.message}</p>`;
        }
    }

    // --- Init ---
    checkAuth();
});
