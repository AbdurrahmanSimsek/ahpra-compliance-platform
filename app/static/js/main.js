// Main JavaScript for Ahpra Compliance Audit Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert:not(.alert-permanent)');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const alert = new bootstrap.Alert(message);
            alert.close();
        }, 5000);
    });
    
    // Add confirmation for sensitive actions
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const confirmMessage = this.dataset.confirm || 'Are you sure you want to proceed?';
            if (!confirm(confirmMessage)) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Dynamic year in footer copyright
    const yearElement = document.querySelector('.copyright-year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
    
    // Handle tab state persistence using URL hash
    const triggerTabList = [].slice.call(document.querySelectorAll('a[data-bs-toggle="tab"]'));
    
    // Use URL hash to activate tab if present
    let activeTab = window.location.hash;
    if (activeTab) {
        const triggerEl = document.querySelector(`a[href="${activeTab}"]`);
        if (triggerEl) {
            const tab = new bootstrap.Tab(triggerEl);
            tab.show();
        }
    }
    
    // Update URL hash when tab is clicked
    triggerTabList.forEach(function(triggerEl) {
        triggerEl.addEventListener('shown.bs.tab', function(event) {
            window.location.hash = event.target.getAttribute('href');
        });
    });
    
    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Remove non-numeric characters except decimal point
            let value = this.value.replace(/[^0-9.]/g, '');
            
            // Ensure only one decimal point
            const decimalPoints = value.match(/\./g);
            if (decimalPoints && decimalPoints.length > 1) {
                const parts = value.split('.');
                value = parts[0] + '.' + parts.slice(1).join('');
            }
            
            // Format with 2 decimal places
            if (value.includes('.')) {
                const parts = value.split('.');
                value = parts[0] + '.' + parts[1].slice(0, 2);
            }
            
            this.value = value;
        });
    });
    
    // Code copy functionality
    const copyButtons = document.querySelectorAll('.copy-code-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const codeBlock = this.closest('.code-container').querySelector('code, pre');
            const textArea = document.createElement('textarea');
            textArea.value = codeBlock.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            // Update button text temporarily
            const originalText = this.textContent;
            this.textContent = 'Copied!';
            setTimeout(() => {
                this.textContent = originalText;
            }, 2000);
        });
    });
});
