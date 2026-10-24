/**
 * DeviX Academy - Notification Management System
 * Handles:
 *  1. Permission-first workflow (asks permission before triggering device notifications)
 *  2. PWA Service Worker registration for mobile APK status bar notification support
 *  3. Real-time background sync polling (/api/notifications/poll/)
 *  4. Topbar notification bell badge and dropdown updates
 *  5. Web Audio API chime sound on new activity
 */

(function () {
    'use strict';

    let swRegistration = null;
    let lastKnownNotifId = 0;
    let audioCtx = null;

    // Helper: Play a subtle executive bell chime on new activity
    function playNotificationSound() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            if (!audioCtx) audioCtx = new AudioContext();
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }

            const now = audioCtx.currentTime;
            // Primary tone
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, now); // D5
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.15); // A5

            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);

            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now);
            osc.stop(now + 0.5);
        } catch (e) {
            // Audio context restrictions in some webviews
        }
    }

    // Register Service Worker for mobile APK / PWA status bar integration
    async function initServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                swRegistration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('[DeviX] Service Worker registered:', swRegistration.scope);
            } catch (err) {
                console.warn('[DeviX] Service Worker registration failed:', err);
            }
        }
    }

    // Show system device notification (status bar in mobile APK / Android WebView)
    function dispatchDeviceNotification(notif) {
        if (!('Notification' in window) || Notification.permission !== 'granted') {
            return;
        }

        const title = notif.title || 'DeviX Academy Alert';
        const options = {
            body: notif.message || '',
            icon: '/static/images/logo.svg',
            badge: '/static/images/logo.svg',
            tag: 'devix-' + notif.id,
            data: { url: notif.link_url || '/' }
        };

        if (swRegistration && swRegistration.showNotification) {
            // Android APK / PWA Service Worker Status Bar Notification
            swRegistration.showNotification(title, options);
        } else {
            // Standard Web Notification fallback
            try {
                const nativeNotif = new Notification(title, options);
                nativeNotif.onclick = function (event) {
                    event.preventDefault();
                    if (notif.link_url) {
                        window.location.href = notif.link_url;
                    }
                    nativeNotif.close();
                };
            } catch (e) {
                console.warn('[DeviX] Notification dispatch fallback:', e);
            }
        }
    }

    // Initialize Notification Permission Banner
    function checkNotificationPermission() {
        if (!('Notification' in window)) {
            return;
        }

        const banner = document.getElementById('notificationPermissionBanner');
        if (!banner) return;

        if (Notification.permission === 'default') {
            banner.style.display = 'block';
        } else {
            banner.style.display = 'none';
        }
    }

    // Request Notification Permission on user click
    async function requestDeviceNotificationPermission() {
        if (!('Notification' in window)) {
            alert('Notifications are not supported on this browser/device.');
            return;
        }

        try {
            const permission = await Notification.requestPermission();
            const banner = document.getElementById('notificationPermissionBanner');
            if (banner) banner.style.display = 'none';

            if (permission === 'granted') {
                await initServiceWorker();
                // Send a test welcome notification to confirm status bar integration
                dispatchDeviceNotification({
                    id: 'welcome',
                    title: 'DeviX Academy Notifications Enabled',
                    message: 'You will now receive instant status updates for leaves, materials, and messages in your notification bar.',
                    link_url: window.location.pathname
                });
            }
        } catch (e) {
            console.error('[DeviX] Permission request error:', e);
        }
    }

    // Update unread badge in topbar
    function updateBadge(unreadCount) {
        const badge = document.getElementById('notifBadge');
        if (!badge) return;

        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }

    // Prepend new item into dropdown
    function prependNotificationItem(notif) {
        const list = document.getElementById('notifItemsList');
        const placeholder = document.getElementById('noNotifPlaceholder');
        if (placeholder) placeholder.style.display = 'none';
        if (!list) return;

        let iconClass = 'fas fa-info-circle text-secondary';
        if (notif.type.includes('LEAVE')) iconClass = 'fas fa-calendar-check text-warning';
        else if (notif.type.includes('MESSAGE')) iconClass = 'fas fa-comment-dots text-primary';
        else if (notif.type.includes('RESOURCE')) iconClass = 'fas fa-book text-success';
        else if (notif.type.includes('NOTICE')) iconClass = 'fas fa-bullhorn text-info';

        const itemHtml = `
            <a href="${notif.link_url || '#'}" class="dropdown-item px-3 py-2 border-bottom notif-item notif-unread" data-notif-id="${notif.id}">
                <div class="d-flex align-items-start gap-2">
                    <div class="notif-icon-circle mt-1">
                        <i class="${iconClass}"></i>
                    </div>
                    <div class="flex-grow-1 overflow-hidden">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="fw-semibold text-dark small text-truncate" style="max-width: 190px;">${notif.title}</span>
                            <span class="text-muted" style="font-size: 0.7rem;">${notif.created_at || 'Just now'}</span>
                        </div>
                        <div class="text-muted small text-truncate">${notif.message}</div>
                    </div>
                </div>
            </a>
        `;
        list.insertAdjacentHTML('afterbegin', itemHtml);
    }

    // Real-Time Notification Poller
    async function pollNotifications() {
        try {
            const resp = await fetch(`/api/notifications/poll/?last_id=${lastKnownNotifId}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!resp.ok) return;

            const data = await resp.json();
            updateBadge(data.total_unread);

            if (data.has_new && data.notifications.length > 0) {
                // Play audio chime
                playNotificationSound();

                data.notifications.forEach((n) => {
                    if (n.id > lastKnownNotifId) {
                        lastKnownNotifId = n.id;
                    }
                    prependNotificationItem(n);
                    dispatchDeviceNotification(n);
                });
            }
        } catch (e) {
            // Transient network failure / offline
        }
    }

    // CSRF helper for Django AJAX POST
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Mark single notification as read on click
    document.addEventListener('click', async function (e) {
        const item = e.target.closest('.notif-item');
        if (item) {
            const notifId = item.getAttribute('data-notif-id');
            if (notifId && item.classList.contains('notif-unread')) {
                item.classList.remove('notif-unread');
                try {
                    const resp = await fetch(`/api/notifications/${notifId}/mark-read/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        }
                    });
                    if (resp.ok) {
                        const res = await resp.json();
                        updateBadge(res.unread_count);
                    }
                } catch (err) {
                    console.warn(err);
                }
            }
        }
    });

    // Mark all as read button
    document.addEventListener('DOMContentLoaded', function () {
        initServiceWorker();
        checkNotificationPermission();

        // Find highest existing notification ID on page load
        const notifElements = document.querySelectorAll('.notif-item[data-notif-id]');
        notifElements.forEach((el) => {
            const id = parseInt(el.getAttribute('data-notif-id'), 10);
            if (id > lastKnownNotifId) lastKnownNotifId = id;
        });

        // Permission Button Listener
        const enableBtn = document.getElementById('enableNotificationsBtn');
        if (enableBtn) {
            enableBtn.addEventListener('click', requestDeviceNotificationPermission);
        }

        const dismissBtn = document.getElementById('dismissNotificationBannerBtn');
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => {
                const banner = document.getElementById('notificationPermissionBanner');
                if (banner) banner.style.display = 'none';
            });
        }

        // Mark All Read Button Listener
        const markAllBtn = document.getElementById('markAllReadBtn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', async function () {
                try {
                    const resp = await fetch('/api/notifications/mark-all-read/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        }
                    });
                    if (resp.ok) {
                        updateBadge(0);
                        document.querySelectorAll('.notif-item.notif-unread').forEach(el => el.classList.remove('notif-unread'));
                    }
                } catch (err) {
                    console.warn(err);
                }
            });
        }

        // Start background polling every 12 seconds
        setInterval(pollNotifications, 12000);
    });
})();
