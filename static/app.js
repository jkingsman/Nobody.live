/* global Twitch, MicroModal, Settings */
/* eslint no-alert: "off", no-new: "off", no-param-reassign: "off" */
MicroModal.init();

const settings = new Settings();

// set UI customization values and add/remove the classes
const uiSettings = [
  // [setting_name, setting_checkbox_id, body_class]
  ["widePage", "wide_page", "wide"],
  ["minimalPage", "minimal_page", "minimal"],
  ["dualColumn", "dual_column", "dual-column"],
  ["texturedBackground", "textured_background", "background-textured"],
];

// create a nice single string to describe the search ('<include terms> not:<exclude> not:<terms>')
function generateFilterString() {
  const excludeString = settings
    .get("exclude")
    .trim()
    .split(" ")
    .map((term) => (term ? `not:${term}` : ""))
    .join(" ");
  const timeString =
    settings.get("minDuration") > 0
      ? `⏱>${document.getElementById("min-age").value}m`
      : "";

  return `${settings
    .get("include")
    .trim()} ${excludeString} ${timeString}`.trim();
}

// note that this uses the form data so we can ignore the "remember" button
async function getStreams(count = 1) {
  const streamEndpoint = new URL("/stream", settings.get("server"));
  streamEndpoint.searchParams.set("count", count);
  streamEndpoint.searchParams.set("include", settings.get("include"));
  streamEndpoint.searchParams.set("exclude", settings.get("exclude"));
  streamEndpoint.searchParams.set("min_age", settings.get("minDuration", true));
  streamEndpoint.searchParams.set(
    "max_viewers",
    settings.get("maxViewers", true) ? 1 : 0,
  );
  streamEndpoint.searchParams.set(
    "search_operator",
    settings.get("searchOperator"),
  );

  const streamResponse = await fetch(streamEndpoint.href);
  if (streamResponse.status === 503) {
    alert("You're doing that too much! Please slow down.");
    return false;
  }

  if (streamResponse.status >= 400) {
    alert("Search error! Please use a shorter search phrase.");
    MicroModal.show("filter-modal");
    return false;
  }

  const streamJson = await streamResponse.json();
  if (streamJson.length === 0) {
    alert(
      `Uh oh! No streams found. Please broaden your filter (currently '${generateFilterString()}').`,
    );
    MicroModal.show("filter-modal");
    return false;
  }
  return streamJson;
}

function setStreamRuntime() {
  // show stream runtime
  const streamRuntime =
    new Date() - new Date(settings.get("currentStream", true).started_at);
  let streamRuntimeMinutes = Math.round(streamRuntime / (1000 * 60));
  const streamRuntimeHours = Math.floor(streamRuntimeMinutes / 60);
  streamRuntimeMinutes -= streamRuntimeHours * 60;

  let streamRuntimeString = "";
  if (streamRuntimeHours > 0) {
    streamRuntimeString += `${streamRuntimeHours}hr`;
  }

  if (streamRuntimeMinutes > 0) {
    streamRuntimeString += `${streamRuntimeMinutes}min`;
  }

  if (streamRuntimeMinutes === 0 && streamRuntimeHours === 0) {
    streamRuntimeString += "no time at all";
  }

  document.getElementById("stream_duration").innerText = streamRuntimeString;
}

// renders a given stream and handles new-streamer button timeout, history update, etc.
async function renderStream(stream) {
  // no streams provided? Don't derender the current stream, as the fetching logic
  // will handle requesting a search param update for us
  if (!stream) {
    return;
  }

  if (Array.isArray(stream)) {
    // we were given an array; no biggy -- just pop the first off
    // eslint-disable-next-line prefer-destructuring
    stream = stream[0];
  }

  // disables the new streamer button, then reenables after 2 seconds
  document.getElementById("new-streamer-button").disabled = true;
  document.getElementById("new-streamer-button").innerText = "please wait...";
  setTimeout(() => {
    const newButton = document.getElementById("new-streamer-button");
    newButton.disabled = false;
    newButton.innerText = newButton.getAttribute("data-message");
  }, 3000);

  settings.set("currentStream", JSON.stringify(stream));

  // clear and rerender the embed div
  document.getElementById("twitch-embed").innerHTML = "";
  new Twitch.Embed("twitch-embed", {
    width: "100%",
    channel: stream.user_name,
    theme: "dark",
    parent: [window.location.hostname],
  });

  // load and append stream to historical streams
  const usernames = settings.get("streamHistory", true);
  usernames.push(stream.user_name);
  const trimmedUsernames = usernames.slice(-6);
  settings.set("streamHistory", JSON.stringify(trimmedUsernames));

  // rerender list of historical streams
  document.getElementById("stream-list").innerHTML = trimmedUsernames
    .reverse()
    .map((username, idx) => {
      const a = document.createElement("a");
      const linkText = document.createTextNode(username);
      a.appendChild(linkText);
      a.href = `https://www.twitch.tv/${username}`;
      a.target = "_blank";
      a.rel = "noopener";

      if (idx === 0) {
        return `${a.outerHTML} (current)`;
      }

      return a.outerHTML;
    })
    .join(", ");

  // render runtime
  setStreamRuntime();
}

// render a given list of streams to draw thumbnails for
async function renderThumbnails(streamList) {
  const container = document.getElementById("thumbnails");
  if (!streamList) {
    // we have no streams; likely a bad search term
    document
      .querySelectorAll(".bottom-thumbnails-content")
      .forEach((node) => node.classList.add("hidden"));
    return;
  }
  // otherwise remove it in case we hid it
  document
    .querySelectorAll(".bottom-thumbnails-content")
    .forEach((node) => node.classList.remove("hidden"));

  // hide button until we're done, and reinstate and the end
  document
    .querySelectorAll(".new-thumbnails")
    .forEach((button) => button.classList.add("hidden"));
  document
    .querySelectorAll(".loading-throbber")
    .forEach((throbber) => throbber.classList.remove("hidden"));

  container.innerHTML = "";

  streamList.forEach((stream) => {
    // embed inside of an a element so you can ctrl+click to open in a new tab
    const a = document.createElement("a");
    a.href = `${window.location.origin}/?stream=${encodeURIComponent(
      JSON.stringify(stream),
    )}`;
    // override the default so on-page clicks just run the render code
    a.onclick = (event) => {
      if (!event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        renderStream(stream);

        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
      }
    };
    a.rel = "noopener";

    const thumb = document.createElement("img");
    thumb.className = "thumbnail-item";
    thumb.alt = `${stream.user_name}: ${stream.title || "[No title]"}`;
    thumb.title = thumb.alt;
    thumb.src = stream.thumbnail_url
      .replace("{width}", "440")
      .replace("{height}", "248");

    a.appendChild(thumb);
    container.appendChild(a);
  });

  // restore our button listener from our debounce with a bit of rate limit delay
  setTimeout(() => {
    document
      .querySelectorAll(".new-thumbnails")
      .forEach((button) => button.classList.remove("hidden"));
    document
      .querySelectorAll(".loading-throbber")
      .forEach((throbber) => throbber.classList.add("hidden"));
  }, 2000);
}

// load interface customizations from storage -- check the key, then add the class to the body as needed
function setInterfaceCustomizationFromStorage() {
  for (const singleUISetting of uiSettings) {
    const isSet = settings.get(singleUISetting[0], true);
    document.getElementById(singleUISetting[1]).checked = isSet;
    if (isSet) {
      document.body.classList.add(singleUISetting[2]);
    } else {
      document.body.classList.remove(singleUISetting[2]);
    }
  }
}

// update the new streamer and new thumbnails buttons with a description of search criteria when active
function setButtonTextWithFilterDataFromStorage() {
  const streamButton = document.getElementById("new-streamer-button");
  if (
    !settings.get("include").trim() &&
    !settings.get("exclude").trim() &&
    settings.get("minDuration", true) === 0
  ) {
    // we have no filter active; restore things to normal text
    document.querySelectorAll(".new-thumbnails").forEach((button) => {
      button.innerText = "Get new thumbnails";
    });
    document.querySelector("#filter").innerText = "stream filters & settings";
    document.querySelector("#filter").classList.remove("filter-active");

    // always set when-enabled text, but only bother with setting actual text if it's active
    document
      .getElementById("new-streamer-button")
      .setAttribute("data-message", "new streamer");
    if (!streamButton.disabled) {
      document.getElementById("new-streamer-button").innerText = "new streamer";
    }
  } else {
    // we have filters to display
    const searchString = generateFilterString();

    // set thumbnail text, filter status, and new streamer button text
    document.querySelectorAll(".new-thumbnails").forEach((button) => {
      button.innerText = `Get new thumbnails ('${searchString}')`;
    });
    document.querySelector("#filter").innerText = "stream filter active";
    document.querySelector("#filter").classList.add("filter-active");

    document
      .getElementById("new-streamer-button")
      .setAttribute("data-message", `new streamer ('${searchString}')`);

    if (!streamButton.disabled) {
      document.getElementById("new-streamer-button").innerText =
        `new streamer ('${searchString}')`;
    }
  }
}

// write settings form information to storage, update the UI as needed, and possibly refresh stream/thumbs
async function handleFormChange(e) {
  if (e) {
    e.preventDefault();
  }

  // pull data from form
  const shouldRemember = document.getElementById("remember").checked;
  const include = document.getElementById("include").value.trim();
  const exclude = document.getElementById("exclude").value.trim();
  const maxViewers = document.getElementById("show_singles").checked ? 1 : 0;
  const minDuration = Number(document.getElementById("min-age").value);
  const searchOperator = document.querySelector(
    'input[name="search_operator"]:checked',
  ).value;

  const shouldReload =
    settings.get("include") !== include || settings.get("exclude") !== exclude;

  // shouldRemember always needs to go first so include/exclude/etc. get saved
  settings.setBulk({
    shouldRemember,
    include,
    exclude,
    maxViewers,
    minDuration,
    searchOperator,
  });

  // set up interface customizations and button text
  setInterfaceCustomizationFromStorage();
  setButtonTextWithFilterDataFromStorage();

  // load new streams and thumbs if the criteria has changed or if we have no current stream
  // (no current stream means we got no results for the last query, so let's try again)
  if (shouldReload || !settings.get("currentStream", true)) {
    const fetchedStreams = await getStreams(
      settings.get("numberOfThumbnailsToFetch", true) + 1,
    );
    if (fetchedStreams) {
      renderStream(fetchedStreams[0]);
      renderThumbnails(fetchedStreams.slice(1));
    }
  }
}

async function enableDebug() {
  // put this here so google stops showing it since apparently the data-nosnippet and display:none does nothing does nothing >.>
  /* eslint-disable max-len */
  document.getElementById("debug-menu").innerHTML =
    ' | <a id="stream-debug" href="#">show stream debug</a> | <a href="/stats/counts" target="_blank">fill stats</a> | <a href="/stats/games" target="_blank">game stats</a> | <a href="/stats/tags" target="_blank">tag stats</a>';
  /* eslint-enable max-len */
  const debugButton = document.getElementById("stream-debug");
  debugButton.addEventListener("click", () => {
    window.open(
      `${settings.get("server")}/stream/${
        settings.get("currentStream", true).id
      }`,
      "_blank",
    );
  });

  debugButton.addEventListener("touchstart", () => {
    window.open(
      `${settings.get("server")}/stream/${
        settings.get("currentStream", true).id
      }`,
      "_blank",
    );
  });
  settings.set("numberOfThumbnailsToFetch", 64);
}

function updateMOTD() {
  fetch(`${settings.get("server")}/static/motd`, { cache: "no-store" })
    .then((response) => response.text())
    .then((text) => {
      document.getElementById("motd").innerHTML = text;
    });
}

async function initPage() {
  // hook up all event listeners
  document
    .getElementById("new-streamer-button")
    .addEventListener("click", async () => renderStream(await getStreams()));
  document
    .getElementById("save-filter")
    .addEventListener("click", handleFormChange);
  document
    .getElementById("save-filter")
    .addEventListener("touchstart", handleFormChange, { passive: true });
  document
    .getElementById("search-form")
    .addEventListener("submit", handleFormChange);
  // loop throgh the settings, adding an onchange listener to setting[1] (id of the form element for the setting)
  // which sets setting[0], the settings object key for the setting. setInterfaceCustomizationFromStorage will
  // apply setting[2] to the body element when it's enabled
  for (const singleUISetting of uiSettings) {
    document
      .getElementById(singleUISetting[1])
      .addEventListener("change", () => {
        settings.set(
          singleUISetting[0],
          !settings.get(singleUISetting[0], true),
        );
        setInterfaceCustomizationFromStorage();
      });
  }
  document
    .querySelectorAll(".new-thumbnails")
    .forEach((button) =>
      button.addEventListener("click", async () =>
        renderThumbnails(
          await getStreams(settings.get("numberOfThumbnailsToFetch", true)),
        ),
      ),
    );
  document
    .getElementById("debug-trigger")
    .addEventListener("click", enableDebug);
  document
    .getElementById("debug-trigger")
    .addEventListener("touchstart", enableDebug, { passive: true });

  // populate filter UI with values from storage
  document.getElementById("remember").checked = settings.get(
    "shouldRemember",
    true,
  );
  document.getElementById("include").value = settings.get("include");
  document.getElementById("exclude").value = settings.get("exclude");
  document.getElementById("min-age").value = settings.get("minDuration", true);
  document.getElementById("show_singles").checked =
    settings.get("maxViewers", true) === 1;
  document.getElementById("search_all").checked =
    settings.get("searchOperator") === "all";
  document.getElementById("search_any").checked =
    settings.get("searchOperator") === "any";

  // add any interface customization classes to the body
  setInterfaceCustomizationFromStorage();

  // populate new streamer and thumb button with seach criteria if active
  setButtonTextWithFilterDataFromStorage();

  const fetchedStreams = await getStreams(
    settings.get("numberOfThumbnailsToFetch", true) + 1,
  );

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has("stream")) {
    // if we have /?stream=... with raw json then render the specified stream
    renderStream(JSON.parse(urlParams.get("stream")));
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (urlParams.has("force")) {
    // if we have a username, we can force Nobody.live to show it to us
    renderStream({
      user_name: urlParams.get("force"),
      id: `forcedstream-${urlParams.get("force")}`,
      started_at: new Date().toISOString(),
    });
  } else if (fetchedStreams) {
    // nothing specific requested; display a fetched stream if we got any
    renderStream(fetchedStreams[0]);

    // update our "this stream has been running for" every 30s
    setInterval(setStreamRuntime, 30000);
  }

  if (fetchedStreams.length > 1) {
    // render thumbs using the rest of the prefetch
    renderThumbnails(fetchedStreams.slice(1));
  }

  // fetch and render message of the day if we have it
  updateMOTD();
  setInterval(updateMOTD, 3600 * 1000); // 1hr in ms
  // note we can hit the end of this block with no stream running if our search params turned up nothing
}

// clear legacy storage if we have it
if (
  localStorage.getItem("streamHistoryJSON") &&
  !localStorage.getItem("hasMigrated")
) {
  localStorage.clear();
  localStorage.setItem("hasMigrated", true);
}

// load temporary filter into storage if we have one
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has("filter")) {
  settings.set("include", urlParams.get("filter"));
  window.history.replaceState({}, document.title, window.location.pathname);
}

initPage();
