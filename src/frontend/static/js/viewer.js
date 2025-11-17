// Viewer JavaScript for viewing images and PDFs

let images = [];
let currentIndex = 0;
let currentMode = 'images'; // 'images' or 'pdf'

// Initialize viewer
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupExportButton();
    loadImages();
    loadViewerSettings();
});

// Current layout mode
let currentLayout = 'one-by-one';
let slideshowInterval = null;

// Switch between layout modes
function switchLayoutMode(layout) {
    currentLayout = layout;
    const imagesView = document.getElementById('imagesView');
    const pdfView = document.getElementById('pdfView');
    const viewerCenter = document.querySelector('.viewer-center-controls');
    const imageContainer = document.querySelector('.image-container');
    
    // Stop slideshow if active
    stopSlideshow();
    
    // Reset classes
    imagesView.className = 'images-view';
    
    switch (layout) {
        case 'one-by-one':
            imagesView.style.display = 'block';
            pdfView.style.display = 'none';
            viewerCenter.style.display = 'flex';
            showImage(currentIndex);
            break;
            
        case 'scroll':
            imagesView.style.display = 'block';
            pdfView.style.display = 'none';
            viewerCenter.style.display = 'none';
            imagesView.classList.add('scroll-mode');
            showAllImagesScroll();
            break;
            
        case 'grid':
            imagesView.style.display = 'block';
            pdfView.style.display = 'none';
            viewerCenter.style.display = 'none';
            imagesView.classList.add('grid-mode');
            showAllImagesGrid();
            break;
            
        case 'pdf':
            imagesView.style.display = 'none';
            pdfView.style.display = 'block';
            viewerCenter.style.display = 'none';
            loadPDF();
            break;
            
        case 'slideshow':
            imagesView.style.display = 'block';
            pdfView.style.display = 'none';
            viewerCenter.style.display = 'flex';
            startSlideshow();
            break;
            
        case 'compare':
            imagesView.style.display = 'block';
            pdfView.style.display = 'none';
            viewerCenter.style.display = 'flex';
            imagesView.classList.add('compare-mode');
            showCompareMode();
            break;
    }
    
    // Save to localStorage
    localStorage.setItem('viewerLayout', layout);
}

// Load images
async function loadImages() {
    try {
        const response = await fetch(
            `/api/thread/${courseCode}/${threadName}/images`
        );
        const data = await response.json();
        
        if (data.success) {
            images = data.images;
            
            if (images.length > 0) {
                hideLoadingState();
                showImage(0);
                updateNavigationButtons();
            } else {
                showErrorState();
            }
        } else {
            showErrorState();
        }
    } catch (error) {
        console.error('Error loading images:', error);
        showErrorState();
    }
}

// Show specific image
function showImage(index) {
    if (index < 0 || index >= images.length) return;
    
    currentIndex = index;
    const imgElement = document.getElementById('currentImage');
    imgElement.src = images[index];
    
    updateCounter();
    updateNavigationButtons();
}

// Navigate to previous image
function previousImage() {
    if (currentIndex > 0) {
        showImage(currentIndex - 1);
    }
}

// Navigate to next image
function nextImage() {
    if (currentIndex < images.length - 1) {
        showImage(currentIndex + 1);
    }
}

// Setup navigation buttons
function setupNavigation() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    prevBtn.addEventListener('click', previousImage);
    nextBtn.addEventListener('click', nextImage);
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (currentMode === 'images') {
            if (e.key === 'ArrowLeft') {
                previousImage();
            } else if (e.key === 'ArrowRight') {
                nextImage();
            }
        }
    });
}

// Update navigation buttons state
function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    prevBtn.disabled = currentIndex === 0;
    nextBtn.disabled = currentIndex === images.length - 1;
}

// Update image counter
function updateCounter() {
    const counter = document.getElementById('imageCounter');
    counter.textContent = `${currentIndex + 1} / ${images.length}`;
}

// Load PDF
function loadPDF() {
    const pdfFrame = document.getElementById('pdfFrame');
    const pdfView = document.getElementById('pdfView');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const pdfUrl = `/api/thread/${courseCode}/${threadName}/pdf`;
    
    // Show loading state
    loadingState.style.display = 'flex';
    errorState.style.display = 'none';
    pdfView.style.display = 'none';
    
    // Check if PDF exists and load it
    fetch(pdfUrl, { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                // PDF exists, load it
                pdfFrame.src = pdfUrl;
                loadingState.style.display = 'none';
                pdfView.style.display = 'block';
            } else {
                // PDF not found
                console.error('PDF not found (404)');
                loadingState.style.display = 'none';
                showPDFErrorState();
            }
        })
        .catch(error => {
            console.error('Error loading PDF:', error);
            loadingState.style.display = 'none';
            showPDFErrorState();
        });
}

// Show error state specifically for PDF
function showPDFErrorState() {
    const errorState = document.getElementById('errorState');
    const imagesView = document.getElementById('imagesView');
    const pdfView = document.getElementById('pdfView');
    
    errorState.style.display = 'flex';
    imagesView.style.display = 'none';
    pdfView.style.display = 'none';
    
    // Optionally switch back to images mode
    const imagesModeBtn = document.querySelector('[data-mode="images"]');
    if (imagesModeBtn) {
        imagesModeBtn.click();
    }
}

// Hide loading state
function hideLoadingState() {
    const loadingState = document.getElementById('loadingState');
    loadingState.style.display = 'none';
}

// Show error state
function showErrorState() {
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const imagesView = document.getElementById('imagesView');
    const pdfView = document.getElementById('pdfView');
    
    loadingState.style.display = 'none';
    errorState.style.display = 'flex';
    imagesView.style.display = 'none';
    pdfView.style.display = 'none';
}

// Viewer Settings Modal
function openViewerSettings() {
    const modal = document.getElementById('viewerSettingsModal');
    modal.style.display = 'flex';
    
    // Highlight current layout
    document.querySelectorAll('.layout-option').forEach(opt => {
        opt.classList.remove('active');
        if (opt.dataset.layout === currentLayout) {
            opt.classList.add('active');
        }
    });
}

function closeViewerSettings() {
    const modal = document.getElementById('viewerSettingsModal');
    modal.style.display = 'none';
}

// Setup layout options
function setupLayoutOptions() {
    const layoutOptions = document.querySelectorAll('.layout-option');
    const slideshowSettings = document.getElementById('slideshowSettings');
    
    layoutOptions.forEach(opt => {
        opt.addEventListener('click', () => {
            const layout = opt.dataset.layout;
            switchLayoutMode(layout);
            
            // Show/hide slideshow settings
            if (layout === 'slideshow') {
                slideshowSettings.style.display = 'block';
            } else {
                slideshowSettings.style.display = 'none';
            }
            
            // Update active state
            layoutOptions.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            
            // Close modal
            closeViewerSettings();
        });
    });
}

// Show all images in scroll mode
function showAllImagesScroll() {
    const container = document.querySelector('.image-container');
    container.innerHTML = '';
    
    images.forEach((imgSrc, index) => {
        const img = document.createElement('img');
        img.src = imgSrc;
        img.alt = `Image ${index + 1}`;
        container.appendChild(img);
    });
}

// Show all images in grid mode
function showAllImagesGrid() {
    const container = document.querySelector('.image-container');
    container.innerHTML = '';
    
    images.forEach((imgSrc, index) => {
        const gridItem = document.createElement('div');
        gridItem.className = 'grid-item';
        
        const img = document.createElement('img');
        img.src = imgSrc;
        img.alt = `Image ${index + 1}`;
        
        gridItem.appendChild(img);
        gridItem.addEventListener('click', () => {
            currentIndex = index;
            switchLayoutMode('one-by-one');
        });
        
        container.appendChild(gridItem);
    });
}

// Show compare mode (2 images side by side)
function showCompareMode() {
    const container = document.querySelector('.image-container');
    container.innerHTML = '';
    
    const img1 = document.createElement('img');
    img1.className = 'compare-image';
    img1.src = images[currentIndex] || '';
    
    const img2 = document.createElement('img');
    img2.className = 'compare-image';
    img2.src = images[currentIndex + 1] || images[0];
    
    container.appendChild(img1);
    container.appendChild(img2);
}

// Slideshow functionality
function startSlideshow() {
    const intervalSeconds = parseInt(document.getElementById('slideshowInterval')?.value || '3');
    
    stopSlideshow();
    showImage(currentIndex);
    
    slideshowInterval = setInterval(() => {
        if (currentIndex < images.length - 1) {
            showImage(currentIndex + 1);
        } else {
            showImage(0);
        }
    }, intervalSeconds * 1000);
}

function stopSlideshow() {
    if (slideshowInterval) {
        clearInterval(slideshowInterval);
        slideshowInterval = null;
    }
}

// Export PDF button
function setupExportButton() {
    const exportBtn = document.getElementById('exportPdfBtn');
    exportBtn.addEventListener('click', () => {
        const pdfUrl = `/api/thread/${courseCode}/${threadName}/pdf`;
        window.open(pdfUrl, '_blank');
    });
}

// Load and save viewer settings
function loadViewerSettings() {
    const savedLayout = localStorage.getItem('viewerLayout');
    if (savedLayout) {
        currentLayout = savedLayout;
    }
    setupLayoutOptions();
}

// Close modal on outside click
window.addEventListener('click', (e) => {
    const modal = document.getElementById('viewerSettingsModal');
    if (e.target === modal) {
        closeViewerSettings();
    }
});
