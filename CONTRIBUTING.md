# Contributing

I'm generally open to bug fixes and optimizations. Please raise any feature requests in an Issue first; I'm somewhat picky about my vision for the site and don't want someone to sink time into a feature that I'd rather not merge (although you're always welcome to fork!).

I will not accept visual redesigns or major alterations to look and feel to the site, although feel free to raise an issue to voice your ideas!

Please format all Python using Black (installed with requirements) and ensure you pass Pylint at 10/10 before PRing.

Please install eslint and associated packages (outlined below) and ensure all JS meets eslint/airbnb standards.

## Linting

```bash
# install requirements
pip install -r requirements.txt
npm install eslint eslint-config-airbnb-base eslint-plugin-html eslint-plugin-import

# lint
black *.py
pylint *.py
./node_modules/.bin/eslint --fix --ext .html,.js static/*.html static/storage.js static/app.js
```
