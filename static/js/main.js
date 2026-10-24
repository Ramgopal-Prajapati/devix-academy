/**
 * DeviX Academy - Core Client Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle & Backdrop Handling
    const sidebarToggleBtn = document.getElementById('sidebarToggle');
    const sidebarCloseBtn = document.getElementById('sidebarToggleClose');
    const sidebar = document.querySelector('.app-sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    function openSidebar() {
        if (sidebar) sidebar.classList.add('show-mobile');
        if (backdrop) backdrop.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('show-mobile');
        if (backdrop) backdrop.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (sidebar && sidebar.classList.contains('show-mobile')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeSidebar();
        });
    }

    if (backdrop) {
        backdrop.addEventListener('click', () => {
            closeSidebar();
        });
    }

    // Auto close sidebar when a navigation link is clicked on mobile
    const navLinks = document.querySelectorAll('.nav-item-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 992) {
                closeSidebar();
            }
        });
    });

    // 2. Avatar / Profile Picture Upload Live Preview
    const avatarInputs = document.querySelectorAll('.avatar-file-input');
    avatarInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = this.files[0];
            const targetImgId = this.dataset.previewTarget;
            const targetImg = document.getElementById(targetImgId);
            if (file && targetImg) {
                // Validate file type
                if (!file.type.startsWith('image/')) {
                    alert('Please select a valid image file (PNG, JPG, JPEG, WEBP).');
                    this.value = '';
                    return;
                }
                // Validate file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    alert('Image size exceeds 5MB. Please upload a smaller photo.');
                    this.value = '';
                    return;
                }
                const reader = new FileReader();
                reader.onload = function(evt) {
                    targetImg.src = evt.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // 3. Dynamic Course Dropdown Filter based on Department (Fetch API)
    const deptSelect = document.getElementById('id_department');
    const courseSelect = document.getElementById('id_course');
    if (deptSelect && courseSelect) {
        deptSelect.addEventListener('change', function() {
            const deptId = this.value;
            courseSelect.innerHTML = '<option value="">Loading courses...</option>';
            courseSelect.disabled = true;

            const url = deptId ? `/api/courses/?department=${encodeURIComponent(deptId)}` : '/api/courses/';
            fetch(url)
                .then(response => {
                    if (!response.ok) throw new Error('Network error fetching courses');
                    return response.json();
                })
                .then(data => {
                    courseSelect.innerHTML = '<option value="">-- Select Course --</option>';
                    // DRF can return { results: [...] } if paginated, or direct list [...]
                    const courses = Array.isArray(data) ? data : (data.results || []);
                    if (courses.length === 0) {
                        courseSelect.innerHTML = '<option value="">No courses available in this department</option>';
                    } else {
                        courses.forEach(c => {
                            const opt = document.createElement('option');
                            opt.value = c.id;
                            const dur = c.duration ? ` (${c.duration})` : '';
                            opt.textContent = `${c.name}${dur}`;
                            courseSelect.appendChild(opt);
                        });
                    }
                    courseSelect.disabled = false;
                })
                .catch(err => {
                    console.error('Error fetching courses:', err);
                    courseSelect.innerHTML = '<option value="">Failed to load courses</option>';
                    courseSelect.disabled = false;
                });
        });
    }

    // 4. Delete Confirmation Modal Wiring
    const deleteModal = document.getElementById('deleteConfirmModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const actionUrl = button.getAttribute('data-delete-url');
            const itemName = button.getAttribute('data-item-name');
            const itemType = button.getAttribute('data-item-type') || 'item';

            const form = deleteModal.querySelector('#deleteConfirmForm');
            const nameSpan = deleteModal.querySelector('#deleteItemName');
            const typeSpan = deleteModal.querySelector('#deleteItemType');

            if (form) form.action = actionUrl;
            if (nameSpan) nameSpan.textContent = itemName;
            if (typeSpan) typeSpan.textContent = itemType;
        });
    }

    // 5. Copy to Clipboard Functionality
    document.querySelectorAll('.btn-copy-clipboard').forEach(btn => {
        btn.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy-text');
            if (navigator.clipboard && textToCopy) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const origHtml = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check text-success me-1"></i> Copied!';
                    setTimeout(() => {
                        this.innerHTML = origHtml;
                    }, 2000);
                }).catch(err => {
                    console.error('Copy failed:', err);
                });
            }
        });
    });

    // 6. Auto-dismiss alerts after 5 seconds
    const autoAlerts = document.querySelectorAll('.alert-dismissible');
    autoAlerts.forEach(alertEl => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });
});
