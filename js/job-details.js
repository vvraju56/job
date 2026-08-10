(function () {
  var jobDetail = document.getElementById("job-detail");
  var applyLink = document.getElementById("apply-link");
  var companyBox = document.getElementById("company-box");
  var yearEl = document.getElementById("year");

  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  var params = new URLSearchParams(window.location.search);
  var job = getJobById(params.get("id"));

  function listHtml(items) {
    return (
      "<ul>" +
      items
        .map(function (item) {
          return "<li>" + item + "</li>";
        })
        .join("") +
      "</ul>"
    );
  }

  if (!job) {
    jobDetail.innerHTML =
      '<h1>Job not found</h1><p style="color: var(--text-muted);">The job you are looking for does not exist.</p><a class="btn" href="index.html" style="margin-top: 16px;">Browse Jobs</a>';
    return;
  }

  jobDetail.innerHTML =
    '<h1>' + job.title + "</h1>" +
    '<p class="job-company" style="font-size: 16px; margin-bottom: 8px;">' + job.company + "</p>" +
    '<div class="detail-meta">' +
    '<span class="tag gray">📍 ' + job.location + "</span>" +
    '<span class="tag gray">' + job.type + "</span>" +
    '<span class="tag gray">Experience: ' + job.experience + "</span>" +
    '<span class="tag gray">' + job.posted + "</span>" +
    (job.remote ? '<span class="tag">Remote Friendly</span>' : "") +
    "</div>" +
    '<p class="salary" style="font-size: 18px;">' + job.salary + "</p>" +
    '<div class="detail-section">' +
    "<h2>About the role</h2><p>" + job.description + "</p>" +
    "</div>" +
    '<div class="detail-section"><h2>Responsibilities</h2>' +
    listHtml(job.responsibilities) +
    "</div>" +
    '<div class="detail-section"><h2>Requirements</h2>' +
    listHtml(job.requirements) +
    "</div>" +
    '<div class="detail-section"><h2>What we offer</h2>' +
    listHtml(job.perks) +
    "</div>" +
    '<div class="apply-box">' +
    "<h3>Interested in this role?</h3>" +
    '<p>Apply now and get your application reviewed quickly.</p>' +
    '<a class="btn" href="apply.html?jobId=' + job.id + '">Apply Now</a>' +
    "</div>";

  applyLink.href = "apply.html?jobId=" + job.id;

  companyBox.innerHTML =
    "<strong>" + job.company + "</strong><br />" +
    "<p style='margin-top: 6px;'>" +
    "A growing company offering roles like <em>" + job.title + "</em> at <strong>" + job.location + "</strong>.<br /><br />" +
    "Type: " + job.type + "<br />" +
    "Posted: " + job.posted +
    "</p>";
})();
