/**
 * DeviX Academy - Progressive Web App Service Worker
 * Handles background push notifications, system status bar tray notifications,
 * and deep-linking when converted to an Android APK or mobile app.
 */

const CACHE_NAME = 'devix-academy-v1';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

// Listen for messages from client windows (e.g. real-time notification poller)
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
        const { title, options } = event.data;
        event.waitUntil(
            self.registration.showNotification(title, {
                icon: options.icon || '/static/images/logo.svg',
                badge: options.badge || '/static/images/logo.svg',
                body: options.body || '',
                tag: options.tag || 'devix-notif-' + Date.now(),
                data: options.data || {},
                vibrate: [200, 100, 200],
                requireInteraction: false
            })
        );
    }
});

// Handle Notification Clicks (Focus or Open Target Page)
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const targetUrl = (event.notification.data && event.notification.data.url) 
        ? event.notification.data.url 
        : '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                if (client.url && 'focus' in client) {
                    client.navigate(targetUrl);
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
