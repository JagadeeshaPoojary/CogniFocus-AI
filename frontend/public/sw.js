/* CogniFocus-AI Service Worker for Teacher Background Notifications */

self.addEventListener('push', function(event) {
    if (!event.data) return;

    let payload = {};
    try {
        payload = event.data.json();
    } catch (e) {
        payload = {
            title: "🚨 Classroom Alert",
            body: event.data.text()
        };
    }

    const title = payload.title || "🚨 CogniFocus-AI Alert";
    const options = {
        body: payload.body || "New classroom alert detected.",
        icon: payload.icon || "/favicon.ico",
        badge: payload.badge || "/favicon.ico",
        data: payload.data || {},
        vibrate: [200, 100, 200],
        requireInteraction: true,
        actions: [
            { action: 'view', title: 'View Alert' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    const alertData = event.notification.data || {};
    const targetUrl = '/alerts';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            for (let i = 0; i < clientList.length; i++) {
                let client = clientList[i];
                if ('focus' in client) {
                    client.postMessage({ type: 'OPEN_ALERT', alert: alertData });
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
