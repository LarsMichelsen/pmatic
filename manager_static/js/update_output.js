function update_output() {
    var xhttp = new XMLHttpRequest();

    xhttp.open("GET", "/ajax_update_output", true);
    xhttp.send();
    xhttp.onreadystatechange = function() {
        if (xhttp.readyState === 4 && xhttp.status === 200) {
            if (xhttp.responseText === "") {
                return;
            }

            // update the content
            var output = document.getElementById("output");
            output.innerHTML = xhttp.responseText.substr(1);

            // automatically scroll down
            output.scrollTop = output.scrollHeight;

            // trigger next update (when still running), otherwise just update once
            var reload = xhttp.responseText.substr(0, 1);
            if (reload === "1") {
                setTimeout(update_output, 1000);
            } else {
                window.location.href = "/run";
            }
        }
    };
}

setTimeout(update_output, 500);
