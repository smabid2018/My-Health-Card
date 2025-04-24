$(document).ready(function() {
  "use strict";
  
  // Set initial state based on screen size
  function initSidebar() {
    if ($(window).width() < 768) {
      // Mobile: Hide sidebar initially
      $("#accordionSidebar").addClass("mobile-sidebar").css({
        "left": "-250px"
      });
      $("#content-wrapper").css("margin-left", "0");
    } else {
      // Desktop: Show sidebar initially
      $("#accordionSidebar").removeClass("mobile-sidebar").css({
        "left": "0"
      });
      $("#content-wrapper").css("margin-left", "");
    }
  }
  
  // Initialize on page load
  initSidebar();
  
  // Toggle sidebar when button is clicked
  $("#sidebarToggleTop, #sidebarToggle").on("click", function(e) {
    e.preventDefault();
    
    if ($(window).width() < 768) {
      // Mobile toggle behavior
      var sidebar = $("#accordionSidebar");
      
      if (sidebar.css("left") === "-250px" || sidebar.css("left") === "-250px") {
        // Show sidebar
        sidebar.animate({left: "0px"}, 300);
        
        // Add overlay if it doesn't exist
        if ($("#sidebarOverlay").length === 0) {
          $("body").append('<div id="sidebarOverlay"></div>');
        }
        $("#sidebarOverlay").fadeIn(300);
        
      } else {
        // Hide sidebar
        sidebar.animate({left: "-250px"}, 300);
        $("#sidebarOverlay").fadeOut(300);
      }
    } else {
      // Desktop toggle behavior (just toggles width)
      $(".sidebar").toggleClass("toggled");
      if ($(".sidebar").hasClass("toggled")) {
        $('.sidebar .collapse').collapse('hide');
      }
    }
  });
  
  // Close sidebar when clicking overlay
  $(document).on("click", "#sidebarOverlay", function() {
    $("#accordionSidebar").animate({left: "-250px"}, 300);
    $(this).fadeOut(300);
  });
  
  // Handle window resize
  $(window).resize(function() {
    initSidebar();
    
    // Additional resize handling
    if ($(window).width() < 768) {
      $('.sidebar .collapse').collapse('hide');
    } else {
      // Reset any mobile-specific styles when returning to desktop
      $("#sidebarOverlay").hide();
    }
  });
  
  // Scroll to top button
  $(document).on('scroll', function() {
    var scrollDistance = $(this).scrollTop();
    if (scrollDistance > 100) {
      $('.scroll-to-top').fadeIn();
    } else {
      $('.scroll-to-top').fadeOut();
    }
  });
  
  // Smooth scrolling using jQuery easing
  $(document).on('click', 'a.scroll-to-top', function(e) {
    var $anchor = $(this);
    $('html, body').animate({
      scrollTop: ($($anchor.attr('href')).offset().top)
    }, 1000, 'easeInOutExpo');
    e.preventDefault();
  });
});