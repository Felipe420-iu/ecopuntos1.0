/* ============================================
   📱 MOBILE NAVIGATION - ECOPUNTOS
   ============================================ */

class MobileNavigation {
    constructor() {
        this.mobileToggle = document.getElementById('mobileNavToggle');
        this.sidebar = document.querySelector('.sidebar');
        this.backdrop = document.getElementById('sidebarBackdrop');
        this.isOpen = false;
        
        this.init();
    }

    init() {
        if (this.mobileToggle) {
            this.mobileToggle.addEventListener('click', () => this.toggleSidebar());
        }
        
        if (this.backdrop) {
            this.backdrop.addEventListener('click', () => this.closeSidebar());
        }
        
        // Cerrar sidebar al cambiar el tamaño de ventana
        window.addEventListener('resize', () => this.handleResize());
        
        // Cerrar sidebar con tecla Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeSidebar();
            }
        });
        
        // Manejar clics en enlaces del sidebar
        this.handleSidebarLinks();
        
        console.log('📱 Mobile Navigation initialized');
    }

    toggleSidebar() {
        if (this.isOpen) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }

    openSidebar() {
        if (!this.sidebar || !this.backdrop) return;
        
        this.isOpen = true;
        
        // Mostrar sidebar
        this.sidebar.classList.add('show');
        this.sidebar.style.transform = 'translateX(0)';
        
        // Mostrar backdrop
        this.backdrop.classList.add('show');
        
        // Bloquear scroll del body
        document.body.style.overflow = 'hidden';
        
        // Cambiar icono del botón
        if (this.mobileToggle) {
            const icon = this.mobileToggle.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-times';
            }
        }
        
        // Animación de entrada
        this.sidebar.style.animation = 'slideInLeft 0.3s ease-out';
        
        // Analytics
        this.trackEvent('sidebar_opened');
        
        console.log('📱 Sidebar opened');
    }

    closeSidebar() {
        if (!this.sidebar || !this.backdrop || !this.isOpen) return;
        
        this.isOpen = false;
        
        // Ocultar sidebar
        this.sidebar.classList.remove('show');
        this.sidebar.style.transform = 'translateX(-100%)';
        
        // Ocultar backdrop
        this.backdrop.classList.remove('show');
        
        // Restaurar scroll del body
        document.body.style.overflow = '';
        
        // Cambiar icono del botón
        if (this.mobileToggle) {
            const icon = this.mobileToggle.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-bars';
            }
        }
        
        // Animación de salida
        this.sidebar.style.animation = 'slideOutLeft 0.3s ease-out';
        
        // Analytics
        this.trackEvent('sidebar_closed');
        
        console.log('📱 Sidebar closed');
    }

    handleResize() {
        // Cerrar sidebar en pantallas grandes
        if (window.innerWidth >= 992 && this.isOpen) {
            this.closeSidebar();
        }
    }

    handleSidebarLinks() {
        const sidebarLinks = document.querySelectorAll('.sidebar a[href]');
        
        sidebarLinks.forEach(link => {
            link.addEventListener('click', () => {
                // Cerrar sidebar después de hacer clic en un enlace (solo en móvil)
                if (window.innerWidth < 992) {
                    setTimeout(() => this.closeSidebar(), 150);
                }
                
                // Analytics
                this.trackEvent('sidebar_link_click', {
                    url: link.href,
                    text: link.textContent.trim()
                });
            });
        });
    }

    trackEvent(eventName, data = {}) {
        if (window.ecoAnalytics) {
            window.ecoAnalytics.trackEvent(`mobile_nav_${eventName}`, data);
        }
    }

    // Métodos públicos para control externo
    isOpened() {
        return this.isOpen;
    }

    forceClose() {
        this.closeSidebar();
    }

    forceOpen() {
        this.openSidebar();
    }
}

/* ============================================
   📬 NOTIFICATION SYSTEM - ECOPUNTOS
   ============================================ */

class NotificationSystem {
    constructor() {
        this.notificationIcon = document.getElementById('notificationIcon');
        this.notificationDropdown = document.getElementById('notificationDropdown');
        this.notificationBadge = document.getElementById('notificationBadge');
        this.notificationList = document.getElementById('notificationList');
        this.notificationCount = document.getElementById('notificationCount');
        this.markAllReadBtn = document.getElementById('markAllRead');
        
        this.isOpen = false;
        this.notifications = [];
        this.pollInterval = null;
        this.lastCheck = null;
        
        this.init();
    }

    init() {
        if (!this.notificationIcon) return;
        
        this.notificationIcon.addEventListener('click', () => this.toggleDropdown());
        
        if (this.markAllReadBtn) {
            this.markAllReadBtn.addEventListener('click', () => this.markAllAsRead());
        }
        
        // Cerrar dropdown al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.notification-container') && this.isOpen) {
                this.closeDropdown();
            }
        });
        
        // Iniciar polling de notificaciones
        this.startPolling();
        
        // Cargar notificaciones iniciales
        this.loadNotifications();
        
        console.log('📬 Notification System initialized');
    }

    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        if (!this.notificationDropdown) return;
        
        this.isOpen = true;
        this.notificationDropdown.classList.add('show');
        
        // Marcar notificaciones como vistas (no leídas)
        this.markAsViewed();
        
        // Analytics
        this.trackEvent('dropdown_opened');
    }

    closeDropdown() {
        if (!this.notificationDropdown) return;
        
        this.isOpen = false;
        this.notificationDropdown.classList.remove('show');
        
        // Analytics
        this.trackEvent('dropdown_closed');
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.notifications = data.notifications || [];
                this.updateUI();
            } else {
                // Cargar notificaciones demo si la API no está disponible
                this.loadDemoNotifications();
            }
        } catch (error) {
            console.log('Loading demo notifications due to:', error.message);
            this.loadDemoNotifications();
        }
    }

    loadDemoNotifications() {
        this.notifications = [
            {
                id: 'demo1',
                tipo: 'canje_aprobado',
                titulo: 'Canje Aprobado',
                mensaje: 'Tu canje de plásticos ha sido aprobado. +50 puntos',
                leido: false,
                created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString()
            },
            {
                id: 'demo2',
                tipo: 'sistema',
                titulo: 'Nuevo Juego Disponible',
                mensaje: 'Ya puedes jugar el nuevo juego de clasificación de vidrios',
                leido: true,
                created_at: new Date(Date.now() - 1000 * 60 * 60).toISOString()
            },
            {
                id: 'demo3',
                tipo: 'logro',
                titulo: '¡Logro Desbloqueado!',
                mensaje: 'Has alcanzado el nivel Eco-Warrior',
                leido: false,
                created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
            }
        ];
        this.updateUI();
    }

    updateUI() {
        this.updateBadge();
        this.updateCount();
        this.renderNotifications();
    }

    updateBadge() {
        if (!this.notificationBadge) return;
        
        const unreadCount = this.notifications.filter(n => !n.leido).length;
        this.notificationBadge.textContent = unreadCount;
        this.notificationBadge.style.display = unreadCount > 0 ? 'flex' : 'none';
    }

    updateCount() {
        if (!this.notificationCount) return;
        
        const unreadCount = this.notifications.filter(n => !n.leido).length;
        this.notificationCount.textContent = unreadCount > 0 ? `${unreadCount} nuevas` : 'Sin notificaciones';
    }

    renderNotifications() {
        if (!this.notificationList) return;
        
        if (this.notifications.length === 0) {
            this.notificationList.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-bell-slash text-muted mb-2" style="font-size: 2rem;"></i>
                    <p class="text-muted mb-0">No hay notificaciones</p>
                </div>
            `;
            return;
        }
        
        this.notificationList.innerHTML = this.notifications
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .map(notification => this.renderNotification(notification))
            .join('');
        
        // Agregar eventos de clic
        this.attachNotificationEvents();
    }

    renderNotification(notification) {
        const isUnread = !notification.leido;
        const timeAgo = this.formatTimeAgo(notification.created_at);
        const iconClass = this.getNotificationIcon(notification.tipo);
        const iconColor = this.getNotificationColor(notification.tipo);
        
        return `
            <div class="notification-item ${isUnread ? 'unread' : ''}" data-id="${notification.id}">
                <div class="notification-item-icon" style="background: ${iconColor};">
                    <i class="fas fa-${iconClass}"></i>
                </div>
                <div class="notification-item-content">
                    <div class="notification-item-title">${notification.titulo}</div>
                    <div class="notification-item-message">${notification.mensaje}</div>
                    <div class="notification-item-time">${timeAgo}</div>
                </div>
                ${isUnread ? '<div class="unread-indicator"></div>' : ''}
            </div>
        `;
    }

    attachNotificationEvents() {
        const notificationItems = this.notificationList.querySelectorAll('.notification-item');
        
        notificationItems.forEach(item => {
            item.addEventListener('click', () => {
                const notificationId = item.dataset.id;
                this.markSingleAsRead(notificationId, item);
            });
        });
    }

    async markSingleAsRead(notificationId, element) {
        // Para notificaciones demo
        if (notificationId.toString().startsWith('demo')) {
            element.classList.remove('unread');
            const unreadIndicator = element.querySelector('.unread-indicator');
            if (unreadIndicator) unreadIndicator.remove();
            
            // Actualizar array local
            const notification = this.notifications.find(n => n.id === notificationId);
            if (notification) notification.leido = true;
            
            this.updateUI();
            return;
        }
        
        try {
            const response = await fetch('/api/notifications/mark-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ notification_id: notificationId })
            });
            
            if (response.ok) {
                element.classList.remove('unread');
                const unreadIndicator = element.querySelector('.unread-indicator');
                if (unreadIndicator) unreadIndicator.remove();
                
                // Actualizar array local
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification) notification.leido = true;
                
                this.updateUI();
                this.trackEvent('notification_read', { id: notificationId });
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                // Marcar todas como leídas localmente
                this.notifications.forEach(n => n.leido = true);
                this.updateUI();
                this.trackEvent('all_notifications_read');
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
            
            // Fallback: marcar localmente
            this.notifications.forEach(n => n.leido = true);
            this.updateUI();
        }
    }

    markAsViewed() {
        // Marcar notificaciones como vistas al abrir el dropdown
        this.trackEvent('notifications_viewed');
    }

    startPolling() {
        // Polling cada 30 segundos
        this.pollInterval = setInterval(() => {
            this.loadNotifications();
        }, 30000);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Hace un momento';
        if (diffInSeconds < 3600) return `Hace ${Math.floor(diffInSeconds / 60)} min`;
        if (diffInSeconds < 86400) return `Hace ${Math.floor(diffInSeconds / 3600)}h`;
        return `Hace ${Math.floor(diffInSeconds / 86400)}d`;
    }

    getNotificationIcon(tipo) {
        const icons = {
            'canje_aprobado': 'check-circle',
            'canje_rechazado': 'times-circle',
            'puntos_agregados': 'coins',
            'sistema': 'info-circle',
            'logro': 'trophy',
            'general': 'bell'
        };
        return icons[tipo] || 'bell';
    }

    getNotificationColor(tipo) {
        const colors = {
            'canje_aprobado': 'var(--success)',
            'canje_rechazado': 'var(--danger)',
            'puntos_agregados': 'var(--warning)',
            'sistema': 'var(--info)',
            'logro': '#ffd700',
            'general': 'var(--primary)'
        };
        return colors[tipo] || 'var(--primary)';
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name=csrf-token]')?.content || '';
    }

    trackEvent(eventName, data = {}) {
        if (window.ecoAnalytics) {
            window.ecoAnalytics.trackEvent(`notification_${eventName}`, data);
        }
    }

    // Métodos públicos
    addNotification(notification) {
        this.notifications.unshift(notification);
        this.updateUI();
    }

    getUnreadCount() {
        return this.notifications.filter(n => !n.leido).length;
    }

    clearAll() {
        this.notifications = [];
        this.updateUI();
    }
}

// Inicialización automática
document.addEventListener('DOMContentLoaded', function() {
    window.mobileNav = new MobileNavigation();
    window.notificationSystem = new NotificationSystem();
});

// Exportar para uso global
window.MobileNavigation = MobileNavigation;
window.NotificationSystem = NotificationSystem;