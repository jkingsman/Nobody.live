import { LiveStream } from '../pages';

function App() {
  return (
    <div className="nl-app__container">
      <nav className="nl-navigation__container">
        <div>LOGO</div>
        <div>SEARCH BOX</div>
        <div>CONFIG?</div>
      </nav>
      <div className="nl-app__content">
        <div className="nl-video-player__container">
          VIDEO HERE
          <LiveStream />
        </div>
        <div>
          CHAT
        </div>
      </div>
      <footer className="nl-footer__container">
        FOOTER HERE
      </footer>
    </div>
  );
}

export default App;
