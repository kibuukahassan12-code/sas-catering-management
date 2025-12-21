/**
 * SAS AI Module JavaScript
 * Handles feature testing, API calls, and UI interactions
 */

(function() {
    'use strict';

    /**
     * Test an AI feature via API
     */
    window.testAIFeature = async function(featureKey, testData = {}) {
        const btn = document.getElementById('test-feature-btn');
        const resultsDiv = document.getElementById('test-results');
        const resultsContent = document.getElementById('test-results-content');
        
        if (!btn || !resultsDiv || !resultsContent) {
            console.error('Test feature elements not found');
            return;
        }
        
        // Disable button and show loading
        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = 'Testing...';
        resultsDiv.style.display = 'none';
        
        try {
            const response = await fetch(`/ai/api/features/${featureKey}/use`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(testData),
            });
            
            const data = await response.json();
            
            // Format results
            resultsContent.textContent = JSON.stringify(data, null, 2);
            resultsDiv.style.display = 'block';
            
            // Scroll to results
            resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
        } catch (error) {
            resultsContent.textContent = 'Error: ' + error.message;
            resultsDiv.style.display = 'block';
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    };

    /**
     * Check feature status
     */
    window.checkFeatureStatus = async function(featureKey) {
        try {
            const response = await fetch(`/ai/api/features/${featureKey}/status`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error checking feature status:', error);
            return { enabled: false, error: error.message };
        }
    };

    /**
     * Initialize AI dashboard interactions
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Add click handlers to feature cards
        const featureCards = document.querySelectorAll('.sas-ai-feature-card:not(.disabled)');
        featureCards.forEach(card => {
            card.addEventListener('click', function() {
                const link = this.querySelector('a');
                if (link) {
                    link.click();
                }
            });
        });

        // Tooltip for disabled features
        const disabledCards = document.querySelectorAll('.sas-ai-feature-card.disabled');
        disabledCards.forEach(card => {
            card.title = 'This feature is currently disabled. Contact an administrator to enable it.';
        });
    });

    /**
     * Toggle AI feature on/off
     */
    window.toggleFeature = async function(featureKey, buttonElement) {
        const currentState = buttonElement.dataset.enabled === 'true';
        const newState = !currentState;
        
        // Disable button during request
        buttonElement.disabled = true;
        const originalContent = buttonElement.innerHTML;
        buttonElement.innerHTML = '⏳';
        
        try {
            const response = await fetch(`/ai/toggle/${featureKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update button state
                buttonElement.dataset.enabled = data.enabled.toString();
                buttonElement.innerHTML = data.enabled ? '🔓' : '🔒';
                
                // Reload page to reflect changes
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                alert('Failed to toggle feature: ' + (data.error || 'Unknown error'));
                buttonElement.innerHTML = originalContent;
            }
        } catch (error) {
            alert('Error toggling feature: ' + error.message);
            buttonElement.innerHTML = originalContent;
        } finally {
            buttonElement.disabled = false;
        }
    };

})();

