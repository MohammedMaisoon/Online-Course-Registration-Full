// script.js - Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const nav = document.querySelector('nav ul');
    
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', function() {
            nav.classList.toggle('active');
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Highlight current navigation item based on URL
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
});

// auth.js - Authentication JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Password visibility toggle
    const passwordFields = document.querySelectorAll('input[type="password"]');
    
    passwordFields.forEach(field => {
        const wrapper = field.parentElement;
        
        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'password-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
        wrapper.appendChild(toggleBtn);
        
        toggleBtn.addEventListener('click', function() {
            const type = field.getAttribute('type') === 'password' ? 'text' : 'password';
            field.setAttribute('type', type);
            
            // Change icon
            toggleBtn.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
        });
    });
    
    // Form validation
    const registerForm = document.querySelector('form[action="/register"]');
    
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            if (password !== confirmPassword) {
                e.preventDefault();
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger';
                alertDiv.textContent = 'Passwords do not match!';
                
                // Remove any existing alerts
                const existingAlerts = document.querySelectorAll('.alert');
                existingAlerts.forEach(alert => alert.remove());
                
                // Add new alert
                registerForm.insertBefore(alertDiv, registerForm.firstChild);
            }
        });
    }
});

// courses.js - Course functionality
document.addEventListener('DOMContentLoaded', function() {
    // Course filter functionality
    const filterForm = document.querySelector('.courses-filter form');
    
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form values
            const category = document.getElementById('category').value;
            const level = document.getElementById('level').value;
            const search = document.getElementById('search').value;
            
            // You would typically make an AJAX request here
            // For demo, we'll just log the values
            console.log('Filtering courses with:', { category, level, search });
            
            // Create URL with query parameters
            const url = `/courses?category=${encodeURIComponent(category)}&level=${encodeURIComponent(level)}&search=${encodeURIComponent(search)}`;
            
            // Redirect or update content
            // window.location.href = url;
            
            // For demo purposes, show a message
            const resultsDiv = document.querySelector('.course-list-grid');
            resultsDiv.innerHTML = `<p>Searching for "${search}" in ${category} category at ${level} level...</p>`;
        });
    }
    
    // Course enrollment functionality
    const enrollButtons = document.querySelectorAll('.btn-enroll');
    
    enrollButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const courseId = this.getAttribute('data-course-id');
            
            // Check if user is logged in
            const isLoggedIn = document.body.classList.contains('logged-in');
            
            if (!isLoggedIn) {
                // Redirect to login
                window.location.href = `/login?redirect=/course/${courseId}`;
                return;
            }
            
            // Enroll in course (AJAX request would go here)
            console.log('Enrolling in course:', courseId);
            
            // Change button state
            this.textContent = 'Enrolled';
            this.classList.add('enrolled');
            this.disabled = true;
        });
    });
});

// dashboard.js - Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if they exist
    const progressChart = document.getElementById('progressChart');
    
    if (progressChart) {
        // Sample chart using a library like Chart.js
        // This is just pseudocode - you'd need to include Chart.js for this to work
        /*
        new Chart(progressChart, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Not Started'],
                datasets: [{
                    data: [65, 25, 10],
                    backgroundColor: ['#c9a227', '#1a3c6e', '#e0e0e0']
                }]
            },
            options: {
                responsive: true,
                cutoutPercentage: 70
            }
        });
        */
    }
    
    // Handle sidebar toggle for mobile
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
});