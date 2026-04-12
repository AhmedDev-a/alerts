/** @odoo-module **/

import { registry } from "@web/core/registry";

const { Component } = owl;

export class NotificationHandler extends Component {
    setup() {
        this.busService = this.env.services.bus_service;
        this.notificationService = this.env.services.notification;

        this.busService.addEventListener("notification", this._onNotification.bind(this));
    }

    _onNotification({ detail }) {
        for (const notif of detail) {

            if (notif.type === "simple_notification") {

                console.log("Received:", notif); // debug

                this.notificationService.add(notif.payload.message, {
                    title: notif.payload.title,
                    type: notif.payload.type || "info",  // 🔥 اللون هنا
                });
            }
        }
    }
}

// تسجيله كـ service (auto start)
registry.category("services").add("notification_handler", {
    start(env) {
        new NotificationHandler(null, { env });
    },
});