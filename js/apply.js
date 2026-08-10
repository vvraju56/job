(function () {
  var form = document.getElementById("apply-form");
  var jobIdInput = document.getElementById("job-id");
  var applyHeading = document.getElementById("apply-heading");
  var applySubtitle = document.getElementById("apply-subtitle");
  var jobSummary = document.getElementById("job-summary");
  var resumeInput = document.getElementById("resume");
  var fileHint = document.getElementById("file-hint");
  var yearEl = document.getElementById("year");

  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  var params = new URLSearchParams(window.location.search);
  var job = getJobById(params.get("id"));

  if (job) {
    jobIdInput.value = job.id;
    applyHeading.textContent = "Apply for " + job.title;
    applySubtitle.textContent = job.company + " · " + job.location + " · " + job.salary;
    jobSummary.innerHTML =
      "<strong>" + job.title + "</strong><br />" +
      "<p style='margin-top: 6px;'>" + job.company + "</p>" +
      "<p>📍 " + job.location + (job.remote ? " (Remote friendly)" : "") + "</p>" +
      "<p>" + job.type + " · " + job.experience + "</p>" +
      "<p class='salary'>" + job.salary + "</p>";
  } else {
    applySubtitle.textContent = "Please pick a job from the listings first.";
    jobSummary.innerHTML = "<p>No job selected. <a href='index.html'>Browse jobs</a>.</p>";
  }

  function showError(inputId) {
    var group = document.getElementById(inputId).closest(".form-group");
    group.classList.add("invalid");
  }

  function clearError(inputId) {
    var group = document.getElementById(inputId).closest(".form-group");
    group.classList.remove("invalid");
  }

  [["full-name"], ["email"], ["phone"], ["experience"], ["resume"]].forEach(function (pair) {
    document.getElementById(pair[0]).addEventListener("input", function () {
      clearError(pair[0]);
    });
    document.getElementById(pair[0]).addEventListener("change", function () {
      clearError(pair[0]);
    });
  });

  resumeInput.addEventListener("change", function () {
    var file = resumeInput.files[0];
    if (file) {
      fileHint.textContent = "✓ " + file.name + " (" + (file.size / 1024).toFixed(0) + " KB)";
    } else {
      fileHint.textContent = "";
    }
  });

  function validate() {
    var valid = true;

    var name = document.getElementById("full-name").value.trim();
    if (name.length < 3) {
      showError("full-name");
      valid = false;
    }

    var email = document.getElementById("email").value.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showError("email");
      valid = false;
    }

    var phone = document.getElementById("phone").value.replace(/[\s()-]/g, "");
    if (!/^\d{10,15}$/.test(phone)) {
      showError("phone");
      valid = false;
    }

    var exp = document.getElementById("experience").value;
    if (!exp) {
      showError("experience");
      valid = false;
    }

    var file = resumeInput.files[0];
    var allowed = ["application/pdf", "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
    if (!file) {
      showError("resume");
      valid = false;
    } else if (file.size > 5 * 1024 * 1024) {
      showError("resume");
      valid = false;
    } else if (allowed.indexOf(file.type) === -1) {
      showError("resume");
      valid = false;
    }

    return valid;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    if (!validate()) {
      var firstInvalid = form.querySelector(".invalid input, .invalid select");
      if (firstInvalid) firstInvalid.focus();
      return;
    }

    var btn = document.getElementById("submit-btn");
    btn.textContent = "Submitting...";
    btn.disabled = true;

    var application = {
      jobId: Number(jobIdInput.value),
      jobTitle: job ? job.title : "",
      company: job ? job.company : "",
      fullName: document.getElementById("full-name").value.trim(),
      email: document.getElementById("email").value.trim(),
      phone: document.getElementById("phone").value.trim(),
      location: document.getElementById("location").value.trim(),
      experience: document.getElementById("experience").value,
      resumeName: resumeInput.files[0] ? resumeInput.files[0].name : "",
      coverLetter: document.getElementById("cover-letter").value.trim(),
      submittedAt: new Date().toISOString()
    };

    setTimeout(function () {
      try {
        var existing = JSON.parse(localStorage.getItem("jobapply_applications") || "[]");
        existing.unshift(application);
        localStorage.setItem("jobapply_applications", JSON.stringify(existing));
        localStorage.setItem("jobapply_last_application", JSON.stringify(application));
      } catch (err) {
        alert("Could not save your application locally. Please try again.");
        btn.textContent = "Submit Application";
        btn.disabled = false;
        return;
      }

      window.location.href = "success.html";
    }, 700);
  });
})();
