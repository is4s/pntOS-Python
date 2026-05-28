#!/usr/bin/env bash
set -xe
ASSETS_TARGET="pntos-cobra/src/pntos/cobra/advanced_plugins/ui/_static/dist/"
SITE_PACKAGES=$(
    "python" -c "import site; print(site.getsitepackages()[0])"
)
mkdir -p pntos-cobra-frontend/src/assets/branding
cp -R $SITE_PACKAGES/branding/. pntos-cobra-frontend/src/assets/branding/
mkdir -p pntos-cobra-frontend/public
cp -f $SITE_PACKAGES/branding/purple-cobra-icon.ico pntos-cobra-frontend/public/purple-cobra-icon.ico

cd pntos-cobra-frontend/

npm install
npm run build
mkdir -p ../$ASSETS_TARGET
cp -R dist/. ../$ASSETS_TARGET
set +x

echo "Cobra UI frontend successfully built to:"
echo $ASSETS_TARGET
