// Main JavaScript for FUO Scraper Homepage

let scrapingTaskId = null;
let scrapingInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCourses();
    setupSearchAutocomplete();
    setupViewToggle();
    loadSettings();
});

// Load all courses
async function loadCourses() {
    try {
        const response = await fetch('/api/courses');
        const data = await response.json();
        
        if (data.success) {
            renderCourses(data.courses);
        }
    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

// Render courses to the grid
function renderCourses(courses) {
    const container = document.getElementById('coursesContainer');
    const emptyState = document.getElementById('emptyState');
    
    container.innerHTML = '';
    
    const courseKeys = Object.keys(courses);
    
    if (courseKeys.length === 0) {
        emptyState.style.display = 'flex';
        return;
    }
    
    emptyState.style.display = 'none';
    
    courseKeys.forEach(courseCode => {
        const threads = courses[courseCode];
        const card = createCourseCard(courseCode, threads);
        container.appendChild(card);
    });
}

// Create a course card
function createCourseCard(courseCode, threads) {
    const card = document.createElement('div');
    card.className = 'course-card';
    
    const header = document.createElement('div');
    header.className = 'course-header';
    
    const codeSpan = document.createElement('div');
    codeSpan.className = 'course-code';
    codeSpan.textContent = courseCode;
    
    const countSpan = document.createElement('div');
    countSpan.className = 'course-count';
    countSpan.textContent = `${threads.length}`;
    
    header.appendChild(codeSpan);
    header.appendChild(countSpan);
    card.appendChild(header);
    
    // Add threads
    threads.forEach(thread => {
        const threadItem = createThreadItem(thread);
        card.appendChild(threadItem);
    });
    
    return card;
}

// Create a thread item
function createThreadItem(thread) {
    const item = document.createElement('div');
    item.className = 'thread-item';
    
    const name = document.createElement('div');
    name.className = 'thread-name';
    name.textContent = thread.name;
    
    item.appendChild(name);
    
    // Click to view - entire card is clickable
    item.addEventListener('click', (e) => {
        e.stopPropagation();
        window.location.href = `/view/${thread.course_code}/${thread.name}`;
    });
    
    return item;
}

// Settings Modal functions
function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'flex';
}

function closeSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'none';
}

// Close modal on outside click
window.addEventListener('click', (e) => {
    const modal = document.getElementById('settingsModal');
    if (e.target === modal) {
        closeSettingsModal();
    }
});

// Start scraping
async function startScrape() {
    const urlInput = document.getElementById('scrapeUrl');
    const url = urlInput.value.trim();
    const statusDiv = document.getElementById('scrapeStatus');
    const progressBar = document.getElementById('progressBar');
    const scrapeButton = document.getElementById('scrapeButton');
    const headlessCheckbox = document.getElementById('headlessMode');
    
    if (!url) {
        showStatus('error', 'Vui lòng nhập URL');
        return;
    }
    
    if (!url.startsWith('https://fuoverflow.com/')) {
        showStatus('error', 'URL không hợp lệ. Phải là link từ FUOverflow.');
        return;
    }
    
    try {
        scrapeButton.disabled = true;
        showStatus('info', 'Đang bắt đầu scrape...');
        
        const headless = headlessCheckbox ? headlessCheckbox.checked : false;
        const itemDelay = parseInt(document.getElementById('itemDelay')?.value || '2');
        const pageLoadTimeout = parseInt(document.getElementById('pageLoadTimeout')?.value || '10');
        const elementTimeout = parseInt(document.getElementById('elementTimeout')?.value || '10');
        
        // Save settings to localStorage
        saveSettings(headless, itemDelay, pageLoadTimeout, elementTimeout);
        
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: url,
                headless: headless,
                item_delay: itemDelay,
                page_load_timeout: pageLoadTimeout,
                element_timeout: elementTimeout
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            scrapingTaskId = data.task_id;
            const progressBarContainer = document.getElementById('progressBarContainer');
            if (progressBarContainer) {
                progressBarContainer.style.display = 'block';
            }
            showStatus('info', 'Đang scrape... Vui lòng chờ.');
            
            // Start polling for progress
            scrapingInterval = setInterval(checkScrapingProgress, 2000);
        } else {
            showStatus('error', data.error || 'Không thể bắt đầu scrape');
            scrapeButton.disabled = false;
        }
    } catch (error) {
        showStatus('error', 'Lỗi: ' + error.message);
        scrapeButton.disabled = false;
    }
}

// Check scraping progress
async function checkScrapingProgress() {
    if (!scrapingTaskId) return;
    
    try {
        const response = await fetch(`/api/scrape/status/${scrapingTaskId}`);
        const data = await response.json();
        
        if (data.success) {
            const task = data.task;
            
            if (task.status === 'running') {
                updateProgress(task.progress, task.total);
            } else if (task.status === 'completed') {
                clearInterval(scrapingInterval);
                updateProgress(100, 100);
                showStatus('success', `Scrape hoàn thành! Đã tải ${task.result.image_count} ảnh.`);
                document.getElementById('scrapeButton').disabled = false;
                document.getElementById('scrapeUrl').value = '';
                
                // Reload courses
                setTimeout(() => {
                    loadCourses();
                    const progressBarContainer = document.getElementById('progressBarContainer');
                    if (progressBarContainer) {
                        progressBarContainer.style.display = 'none';
                    }
                }, 2000);
            } else if (task.status === 'error') {
                clearInterval(scrapingInterval);
                showStatus('error', 'Lỗi: ' + task.error);
                document.getElementById('scrapeButton').disabled = false;
                const progressBarContainer = document.getElementById('progressBarContainer');
                if (progressBarContainer) {
                    progressBarContainer.style.display = 'none';
                }
            }
        }
    } catch (error) {
        console.error('Error checking progress:', error);
    }
}

// Update progress bar with segments
function updateProgress(current, total) {
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = progressBarContainer?.querySelector('.progress-text');
    
    if (!progressBar || !progressText) {
        console.error('Progress elements not found');
        return;
    }
    
    // Create segments if not already created
    if (!progressBar.querySelector('.progress-segment')) {
        progressBar.innerHTML = '';
        for (let i = 0; i < total; i++) {
            const segment = document.createElement('div');
            segment.className = 'progress-segment';
            segment.dataset.index = i;
            progressBar.appendChild(segment);
        }
    }
    
    // Update segments
    const segments = progressBar.querySelectorAll('.progress-segment');
    segments.forEach((segment, index) => {
        segment.classList.remove('completed', 'current');
        if (index < current) {
            segment.classList.add('completed');
        } else if (index === current) {
            segment.classList.add('current');
        }
    });
    
    const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
    progressText.textContent = `${current} / ${total} (${percentage}%)`;
}

// Show status message
function showStatus(type, message) {
    const statusDiv = document.getElementById('scrapeStatus');
    statusDiv.className = `scrape-status ${type}`;
    statusDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
}

// Setup search autocomplete
function setupSearchAutocomplete() {
    const searchInput = document.getElementById('searchInput');
    const suggestionsDropdown = document.getElementById('suggestions');
    let debounceTimer;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            suggestionsDropdown.classList.remove('show');
            return;
        }
        
        debounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success && data.suggestions.length > 0) {
                    renderSuggestions(data.suggestions);
                } else {
                    suggestionsDropdown.classList.remove('show');
                }
            } catch (error) {
                console.error('Error fetching suggestions:', error);
            }
        }, 300);
    });
    
    // Handle search on Enter
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch(searchInput.value);
            suggestionsDropdown.classList.remove('show');
        }
    });
    
    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestionsDropdown.contains(e.target)) {
            suggestionsDropdown.classList.remove('show');
        }
    });
}

// Render search suggestions
function renderSuggestions(suggestions) {
    const suggestionsDropdown = document.getElementById('suggestions');
    suggestionsDropdown.innerHTML = '';
    
    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.innerHTML = `<i class="fas fa-search"></i> ${suggestion}`;
        
        item.addEventListener('click', () => {
            document.getElementById('searchInput').value = suggestion;
            performSearch(suggestion);
            suggestionsDropdown.classList.remove('show');
        });
        
        suggestionsDropdown.appendChild(item);
    });
    
    suggestionsDropdown.classList.add('show');
}

// Perform search
async function performSearch(query) {
    if (!query.trim()) return;
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Group results by course code
            const grouped = {};
            data.results.forEach(thread => {
                if (!grouped[thread.course_code]) {
                    grouped[thread.course_code] = [];
                }
                grouped[thread.course_code].push(thread);
            });
            
            renderCourses(grouped);
        }
    } catch (error) {
        console.error('Error searching:', error);
    }
}

// Refresh courses
function refreshCourses() {
    const refreshBtn = document.querySelector('.nav-actions .nav-button');
    refreshBtn.style.animation = 'spin 1s ease';
    
    loadCourses();
    
    setTimeout(() => {
        refreshBtn.style.animation = '';
    }, 1000);
}

// Toggle theme (placeholder for future)
function toggleTheme() {
    // Can implement light/dark theme toggle here
    console.log('Theme toggle - coming soon!');
}

// Setup view toggle
function setupViewToggle() {
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            toggleBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const view = btn.dataset.view;
            const container = document.getElementById('coursesContainer');
            
            if (view === 'list') {
                container.style.gridTemplateColumns = '1fr';
            } else {
                container.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
            }
        });
    });
}

// Save settings to localStorage
function saveSettings(headless, itemDelay, pageLoadTimeout, elementTimeout) {
    const settings = {
        headless,
        itemDelay,
        pageLoadTimeout,
        elementTimeout
    };
    localStorage.setItem('fuoScraperSettings', JSON.stringify(settings));
}

// Load settings from localStorage
function loadSettings() {
    const savedSettings = localStorage.getItem('fuoScraperSettings');
    
    if (savedSettings) {
        try {
            const settings = JSON.parse(savedSettings);
            
            // Apply saved settings to UI
            const headlessCheckbox = document.getElementById('headlessMode');
            const itemDelayInput = document.getElementById('itemDelay');
            const pageLoadTimeoutInput = document.getElementById('pageLoadTimeout');
            const elementTimeoutInput = document.getElementById('elementTimeout');
            
            if (headlessCheckbox) headlessCheckbox.checked = settings.headless !== undefined ? settings.headless : true;
            if (itemDelayInput) itemDelayInput.value = settings.itemDelay || 2;
            if (pageLoadTimeoutInput) pageLoadTimeoutInput.value = settings.pageLoadTimeout || 5;
            if (elementTimeoutInput) elementTimeoutInput.value = settings.elementTimeout || 5;
        } catch (e) {
            console.error('Error loading settings:', e);
        }
    } else {
        // Set defaults if no saved settings
        const headlessCheckbox = document.getElementById('headlessMode');
        const itemDelayInput = document.getElementById('itemDelay');
        const pageLoadTimeoutInput = document.getElementById('pageLoadTimeout');
        const elementTimeoutInput = document.getElementById('elementTimeout');
        
        if (headlessCheckbox) headlessCheckbox.checked = true;
        if (itemDelayInput) itemDelayInput.value = 2;
        if (pageLoadTimeoutInput) pageLoadTimeoutInput.value = 5;
        if (elementTimeoutInput) elementTimeoutInput.value = 5;
    }
}

// Reset settings to default
function resetSettings() {
    document.getElementById('headlessMode').checked = true;
    document.getElementById('itemDelay').value = 2;
    document.getElementById('pageLoadTimeout').value = 5;
    document.getElementById('elementTimeout').value = 5;
    
    // Save defaults
    saveSettings(true, 2, 5, 5);
    
    showStatus('info', 'Đã reset về cài đặt mặc định');
}

// Save settings and close modal
function saveSettingsAndClose() {
    const headless = document.getElementById('headlessMode').checked;
    const itemDelay = parseInt(document.getElementById('itemDelay').value);
    const pageLoadTimeout = parseInt(document.getElementById('pageLoadTimeout').value);
    const elementTimeout = parseInt(document.getElementById('elementTimeout').value);
    
    // Save to localStorage
    saveSettings(headless, itemDelay, pageLoadTimeout, elementTimeout);
    
    // Show success message
    showStatus('success', 'Đã lưu cài đặt thành công!');
    
    // Close modal
    closeSettingsModal();
}
