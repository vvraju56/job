(function () {
  var searchInput = document.getElementById("search-input");
  var locationInput = document.getElementById("location-input");
  var searchForm = document.getElementById("search-form");
  var filterType = document.getElementById("filter-type");
  var filterExp = document.getElementById("filter-exp");
  var filterRemote = document.getElementById("filter-remote");
  var jobList = document.getElementById("job-list");
  var resultCount = document.getElementById("result-count");
  var yearEl = document.getElementById("year");

  var AD_EVERY = 3;

  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  function cardHtml(job) {
    return (
      '<article class="job-card">' +
      '<div class="job-card-top">' +
      '<h3 class="job-title"><a href="job.html?id=' + job.id + '">' + job.title + "</a></h3>" +
      '<p class="job-company">' + job.company + " · " + job.location + "</p>" +
      '<p class="salary">' + job.salary + "</p>" +
      '<div class="job-meta">' +
      job.tags
        .map(function (tag) {
          return '<span class="tag">' + tag + "</span>";
        })
        .join("") +
      '<span class="tag gray">' + job.type + "</span>" +
      (job.remote ? '<span class="tag gray">Remote</span>' : "") +
      "</div>" +
      "</div>" +
      '<a class="btn" href="job.html?id=' + job.id + '">Apply Now</a>' +
      "</article>"
    );
  }

  function adCardHtml() {
    return (
      '<div class="ad-unit">' +
      '<div class="ad-label">Advertisement</div>' +
      '<ins class="adsbygoogle" style="display:block" ' +
      'data-ad-client="ca-pub-3575487613290267" ' +
      'data-ad-slot="INFEED_SLOT_ID" ' +
      'data-ad-format="auto" data-full-width-responsive="true"></ins>' +
      '<script>(adsbygoogle = window.adsbygoogle || []).push({});<\/script>' +
      "</div>"
    );
  }

  function getFilteredJobs() {
    var query = (searchInput.value || "").trim().toLowerCase();
    var loc = (locationInput.value || "").trim().toLowerCase();
    var type = filterType.value;
    var exp = filterExp.value;
    var remoteOnly = filterRemote.checked;

    return JOBS.filter(function (job) {
      var haystack = (job.title + " " + job.company + " " + job.tags.join(" ")).toLowerCase();
      if (query && haystack.indexOf(query) === -1) return false;
      if (loc && job.location.toLowerCase().indexOf(loc) === -1 && !(loc.indexOf("remote") !== -1 && job.remote)) return false;
      if (type && job.type !== type) return false;
      if (exp && job.experience !== exp) return false;
      if (remoteOnly && !job.remote) return false;
      return true;
    });
  }

  function render() {
    var jobs = getFilteredJobs();
    resultCount.textContent = jobs.length + " job" + (jobs.length === 1 ? "" : "s") + " found";

    if (jobs.length === 0) {
      jobList.innerHTML =
        '<div class="empty-state"><p>No jobs match your search.</p><p style="margin-top:8px; font-size:14px;">Try changing your filters.</p></div>';
      return;
    }

    var html = "";
    jobs.forEach(function (job, i) {
      html += cardHtml(job);
      if ((i + 1) % AD_EVERY === 0 && i !== jobs.length - 1) {
        html += adCardHtml();
      }
    });
    jobList.innerHTML = html;
  }

  searchForm.addEventListener("submit", function (e) {
    e.preventDefault();
    render();
  });

  [filterType, filterExp, filterRemote].forEach(function (el) {
    el.addEventListener("change", render);
  });

  searchInput.addEventListener("input", render);
  locationInput.addEventListener("input", render);

  render();
})();
