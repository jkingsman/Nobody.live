function togglePlayer() {
    var checkBox = document.getElementById('checkBox');
    if (checkBox.checked && document.getElementById("main-page").hasAttribute('normal-page')) {
        document.getElementById("main-page").setAttribute('large-player', '');
        document.getElementById("main-page").removeAttribute('normal-page', '');
        removeAttribute
    } else {
        document.getElementById("main-page").setAttribute('normal-page', '');
        document.getElementById("main-page").removeAttribute('large-player', '');
    }
}
/*
 *  document.getElementById('stream-title').innerText = " " + currentStream.title + " " || 'Broadcast';
 *  document.getElementById('streamer-name').innerText = " " + currentStream.user_name + " ";
 *  document.getElementById('stream-game').innerText = " " + currentStream.game_name + " ";
 */

