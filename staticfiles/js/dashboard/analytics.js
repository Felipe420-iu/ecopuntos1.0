/* ============================================
   📊 ANALYTICS DASHBOARD - ECOPUNTOS
   ============================================ */

(function() {
    'use strict';

    // Analytics object
    window.ecoAnalytics = {
        // Track events
        trackEvent: function(eventName, data = {}) {
            if (typeof gtag !== 'undefined') {
                gtag('event', eventName, data);
            }
            console.log(`📊 Analytics: ${eventName}`, data);
        },

        // Track page views
        trackPageView: function(page) {
            this.trackEvent('page_view', {
                page_title: document.title,
                page_location: window.location.href,
                custom_page: page || 'dashboard'
            });
        },

        // Track user interactions
        trackInteraction: function(element, action) {
            this.trackEvent('user_interaction', {
                element: element,
                action: action,
                timestamp: new Date().toISOString()
            });
        },

        // Initialize analytics
        init: function() {
            // Track page load
            this.trackPageView();
            
            // Track clicks on important elements
            document.addEventListener('click', function(e) {
                if (e.target.matches('[data-track]')) {
                    const trackingData = e.target.getAttribute('data-track');
                    window.ecoAnalytics.trackInteraction(trackingData, 'click');
                }
            });

            console.log('✅ Analytics initialized');
        }
    };

    // Auto-initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.ecoAnalytics.init.bind(window.ecoAnalytics));
    } else {
        window.ecoAnalytics.init();
    }
})();