# 项目结构

本文档使用中文概述 `pure-admin-thin` 的目录结构，并说明各文件夹作用。

## 顶层目录说明

- `.husky/`: Git hooks，约束提交与代码质量检查。
- `.vscode/`: VS Code 工作区设置与 Vue 代码片段。
- `build/`: Vite 构建相关的工具函数与插件封装。
- `mock/`: 本地 Mock 接口与登录/刷新 Token 模拟。
- `public/`: 公共静态资源，打包时原样拷贝。
- `src/`: 应用源代码（Vue 3 + TypeScript）。
- `types/`: 全局与模块类型声明。
- 根目录配置文件: lint/format、Vite、Tailwind、TS、Docker、环境变量等。

## src 子目录说明

- `src/api/`: API 请求封装与 Mock 路由。
- `src/assets/`: 图片、SVG、iconfont、登录视觉资源。
- `src/components/`: 复用组件（Re* 前缀）。
- `src/config/`: 应用级配置。
- `src/directives/`: 自定义指令（auth/copy/ripple 等）。
- `src/layout/`: 布局框架与导航/侧边栏等结构。
- `src/plugins/`: 第三方库集成（Element Plus、ECharts）。
- `src/router/`: 路由模块与路由工具。
- `src/store/`: 状态管理模块与工具。
- `src/style/`: 全局样式、主题、Tailwind 入口。
- `src/utils/`: 通用工具（auth/http/存储等）。
- `src/views/`: 页面级视图。
- `src/main.ts`: 应用入口。
- `src/App.vue`: 根组件。

## 完整树结构（排除 `.git/` 和 `node_modules/`）

```
pure-admin-thin/
|-- .husky/
|   |-- _/
|   |   |-- .gitignore
|   |   |-- applypatch-msg
|   |   |-- commit-msg
|   |   |-- h
|   |   |-- husky.sh
|   |   |-- post-applypatch
|   |   |-- post-checkout
|   |   |-- post-commit
|   |   |-- post-merge
|   |   |-- post-rewrite
|   |   |-- pre-applypatch
|   |   |-- pre-auto-gc
|   |   |-- pre-commit
|   |   |-- pre-push
|   |   |-- pre-rebase
|   |   +-- prepare-commit-msg
|   |-- commit-msg
|   |-- common.sh
|   +-- pre-commit
|-- .vscode/
|   |-- extensions.json
|   |-- settings.json
|   |-- vue3.0.code-snippets
|   |-- vue3.2.code-snippets
|   +-- vue3.3.code-snippets
|-- build/
|   |-- cdn.ts
|   |-- compress.ts
|   |-- info.ts
|   |-- optimize.ts
|   |-- plugins.ts
|   +-- utils.ts
|-- mock/
|   |-- asyncRoutes.ts
|   |-- login.ts
|   +-- refreshToken.ts
|-- public/
|   |-- admin.svg
|   |-- favicon.ico
|   |-- logo.svg
|   |-- logo1.svg
|   |-- logo2.svg
|   |-- logo3.svg
|   |-- logo4.svg
|   +-- platform-config.json
|-- src/
|   |-- api/
|   |   |-- list.ts
|   |   |-- mock.ts
|   |   |-- routes.ts
|   |   +-- user.ts
|   |-- assets/
|   |   |-- iconfont/
|   |   |   |-- iconfont.css
|   |   |   |-- iconfont.js
|   |   |   |-- iconfont.json
|   |   |   |-- iconfont.ttf
|   |   |   |-- iconfont.woff
|   |   |   +-- iconfont.woff2
|   |   |-- login/
|   |   |   |-- avatar.svg
|   |   |   |-- avatar1.svg
|   |   |   |-- bg.png
|   |   |   |-- illustration.svg
|   |   |   +-- illustration1.svg
|   |   |-- status/
|   |   |   |-- 403.svg
|   |   |   |-- 404.svg
|   |   |   +-- 500.svg
|   |   |-- svg/
|   |   |   |-- back_top.svg
|   |   |   |-- calendar.svg
|   |   |   |-- dark.svg
|   |   |   |-- day.svg
|   |   |   |-- enter_outlined.svg
|   |   |   |-- exit_screen.svg
|   |   |   |-- full_screen.svg
|   |   |   |-- keyboard_esc.svg
|   |   |   |-- laptop.svg
|   |   |   |-- service.svg
|   |   |   |-- shop.svg
|   |   |   |-- system.svg
|   |   |   +-- user_avatar.svg
|   |   |-- table-bar/
|   |   |   |-- collapse.svg
|   |   |   |-- drag.svg
|   |   |   |-- expand.svg
|   |   |   |-- refresh.svg
|   |   |   +-- settings.svg
|   |   +-- user.jpg
|   |-- components/
|   |   |-- ReAuth/
|   |   |   |-- src/
|   |   |   |   +-- auth.tsx
|   |   |   +-- index.ts
|   |   |-- ReCol/
|   |   |   +-- index.ts
|   |   |-- ReCountTo/
|   |   |   |-- src/
|   |   |   |   |-- normal/
|   |   |   |   |   |-- index.tsx
|   |   |   |   |   +-- props.ts
|   |   |   |   +-- rebound/
|   |   |   |       |-- index.tsx
|   |   |   |       |-- props.ts
|   |   |   |       +-- rebound.css
|   |   |   |-- index.ts
|   |   |   +-- README.md
|   |   |-- ReCropper/
|   |   |   |-- src/
|   |   |   |   |-- svg/
|   |   |   |   |   |-- arrow-down.svg
|   |   |   |   |   |-- arrow-h.svg
|   |   |   |   |   |-- arrow-left.svg
|   |   |   |   |   |-- arrow-right.svg
|   |   |   |   |   |-- arrow-up.svg
|   |   |   |   |   |-- arrow-v.svg
|   |   |   |   |   |-- change.svg
|   |   |   |   |   |-- download.svg
|   |   |   |   |   |-- index.ts
|   |   |   |   |   |-- reload.svg
|   |   |   |   |   |-- rotate-left.svg
|   |   |   |   |   |-- rotate-right.svg
|   |   |   |   |   |-- search-minus.svg
|   |   |   |   |   |-- search-plus.svg
|   |   |   |   |   +-- upload.svg
|   |   |   |   |-- circled.css
|   |   |   |   +-- index.tsx
|   |   |   +-- index.ts
|   |   |-- ReCropperPreview/
|   |   |   |-- src/
|   |   |   |   +-- index.vue
|   |   |   +-- index.ts
|   |   |-- ReDialog/
|   |   |   |-- index.ts
|   |   |   |-- index.vue
|   |   |   +-- type.ts
|   |   |-- ReIcon/
|   |   |   |-- src/
|   |   |   |   |-- hooks.ts
|   |   |   |   |-- iconfont.ts
|   |   |   |   |-- iconifyIconOffline.ts
|   |   |   |   |-- iconifyIconOnline.ts
|   |   |   |   |-- offlineIcon.ts
|   |   |   |   +-- types.ts
|   |   |   +-- index.ts
|   |   |-- RePerms/
|   |   |   |-- src/
|   |   |   |   +-- perms.tsx
|   |   |   +-- index.ts
|   |   |-- RePureTableBar/
|   |   |   |-- src/
|   |   |   |   +-- bar.tsx
|   |   |   +-- index.ts
|   |   |-- ReSegmented/
|   |   |   |-- src/
|   |   |   |   |-- index.css
|   |   |   |   |-- index.tsx
|   |   |   |   +-- type.ts
|   |   |   +-- index.ts
|   |   +-- ReText/
|   |       |-- src/
|   |       |   +-- index.vue
|   |       +-- index.ts
|   |-- config/
|   |   +-- index.ts
|   |-- directives/
|   |   |-- auth/
|   |   |   +-- index.ts
|   |   |-- copy/
|   |   |   +-- index.ts
|   |   |-- longpress/
|   |   |   +-- index.ts
|   |   |-- optimize/
|   |   |   +-- index.ts
|   |   |-- perms/
|   |   |   +-- index.ts
|   |   |-- ripple/
|   |   |   |-- index.scss
|   |   |   +-- index.ts
|   |   +-- index.ts
|   |-- layout/
|   |   |-- components/
|   |   |   |-- lay-content/
|   |   |   |   +-- index.vue
|   |   |   |-- lay-footer/
|   |   |   |   +-- index.vue
|   |   |   |-- lay-frame/
|   |   |   |   +-- index.vue
|   |   |   |-- lay-navbar/
|   |   |   |   +-- index.vue
|   |   |   |-- lay-notice/
|   |   |   |   |-- components/
|   |   |   |   |   |-- NoticeItem.vue
|   |   |   |   |   +-- NoticeList.vue
|   |   |   |   |-- data.ts
|   |   |   |   +-- index.vue
|   |   |   |-- lay-panel/
|   |   |   |   +-- index.vue
|   |   |   |-- lay-search/
|   |   |   |   |-- components/
|   |   |   |   |   |-- SearchFooter.vue
|   |   |   |   |   |-- SearchHistory.vue
|   |   |   |   |   |-- SearchHistoryItem.vue
|   |   |   |   |   |-- SearchModal.vue
|   |   |   |   |   +-- SearchResult.vue
|   |   |   |   |-- index.vue
|   |   |   |   +-- types.ts
|   |   |   |-- lay-setting/
|   |   |   |   +-- index.vue
|   |   |   |-- lay-sidebar/
|   |   |   |   |-- components/
|   |   |   |   |   |-- SidebarBreadCrumb.vue
|   |   |   |   |   |-- SidebarCenterCollapse.vue
|   |   |   |   |   |-- SidebarExtraIcon.vue
|   |   |   |   |   |-- SidebarFullScreen.vue
|   |   |   |   |   |-- SidebarItem.vue
|   |   |   |   |   |-- SidebarLeftCollapse.vue
|   |   |   |   |   |-- SidebarLinkItem.vue
|   |   |   |   |   |-- SidebarLogo.vue
|   |   |   |   |   +-- SidebarTopCollapse.vue
|   |   |   |   |-- NavHorizontal.vue
|   |   |   |   |-- NavMix.vue
|   |   |   |   +-- NavVertical.vue
|   |   |   +-- lay-tag/
|   |   |       |-- components/
|   |   |       |   +-- TagChrome.vue
|   |   |       |-- index.scss
|   |   |       +-- index.vue
|   |   |-- hooks/
|   |   |   |-- useBoolean.ts
|   |   |   |-- useDataThemeChange.ts
|   |   |   |-- useLayout.ts
|   |   |   |-- useMultiFrame.ts
|   |   |   |-- useNav.ts
|   |   |   +-- useTag.ts
|   |   |-- theme/
|   |   |   +-- index.ts
|   |   |-- frame.vue
|   |   |-- index.vue
|   |   |-- redirect.vue
|   |   +-- types.ts
|   |-- plugins/
|   |   |-- echarts.ts
|   |   +-- elementPlus.ts
|   |-- router/
|   |   |-- modules/
|   |   |   |-- account.ts
|   |   |   |-- error.ts
|   |   |   |-- history.ts
|   |   |   |-- home.ts
|   |   |   |-- lists.ts
|   |   |   |-- remaining.ts
|   |   |   +-- upload.ts
|   |   |-- test/
|   |   |   |-- dataset.ts
|   |   |   |-- dataset1.ts
|   |   |   |-- model.ts
|   |   |   |-- model1.ts
|   |   |   |-- modelEval.ts
|   |   |   |-- notice.ts
|   |   |   +-- users.ts
|   |   |-- index.ts
|   |   +-- utils.ts
|   |-- store/
|   |   |-- modules/
|   |   |   |-- app.ts
|   |   |   |-- epTheme.ts
|   |   |   |-- multiTags.ts
|   |   |   |-- permission.ts
|   |   |   |-- settings.ts
|   |   |   +-- user.ts
|   |   |-- index.ts
|   |   |-- types.ts
|   |   +-- utils.ts
|   |-- style/
|   |   |-- dark.scss
|   |   |-- element-plus.scss
|   |   |-- index.scss
|   |   |-- login.css
|   |   |-- reset.scss
|   |   |-- sidebar.scss
|   |   |-- tailwind.css
|   |   +-- transition.scss
|   |-- utils/
|   |   |-- http/
|   |   |   |-- index.ts
|   |   |   +-- types.d.ts
|   |   |-- localforage/
|   |   |   |-- index.ts
|   |   |   +-- types.d.ts
|   |   |-- progress/
|   |   |   +-- index.ts
|   |   |-- auth.ts
|   |   |-- globalPolyfills.ts
|   |   |-- message.ts
|   |   |-- mitt.ts
|   |   |-- preventDefault.ts
|   |   |-- print.ts
|   |   |-- propTypes.ts
|   |   |-- responsive.ts
|   |   |-- sso.ts
|   |   +-- tree.ts
|   |-- views/
|   |   |-- account/
|   |   |   +-- index.vue
|   |   |-- dataset/
|   |   |   +-- index.vue
|   |   |-- error/
|   |   |   |-- 403.vue
|   |   |   |-- 404.vue
|   |   |   +-- 500.vue
|   |   |-- fighting/
|   |   |   +-- index.vue
|   |   |-- history/
|   |   |   |-- data.ts
|   |   |   +-- index.vue
|   |   |-- json/
|   |   |   +-- index.vue
|   |   |-- lists/
|   |   |   +-- index.vue
|   |   |-- login/
|   |   |   |-- components/
|   |   |   |   +-- LoginRegist.vue
|   |   |   |-- utils/
|   |   |   |   |-- motion.ts
|   |   |   |   |-- rule.ts
|   |   |   |   +-- static.ts
|   |   |   +-- index.vue
|   |   |-- model/
|   |   |   +-- index.vue
|   |   |-- modelEval/
|   |   |   +-- index.vue
|   |   |-- notice/
|   |   |   +-- index.vue
|   |   |-- permission/
|   |   |   |-- button/
|   |   |   |   |-- index.vue
|   |   |   |   +-- perms.vue
|   |   |   +-- page/
|   |   |       +-- index.vue
|   |   |-- upload/
|   |   |   |-- data.ts
|   |   |   +-- index.vue
|   |   |-- users/
|   |   |   +-- index.vue
|   |   +-- welcome/
|   |       |-- index.vue
|   |       +-- static.ts
|   |-- App.vue
|   +-- main.ts
|-- types/
|   |-- directives.d.ts
|   |-- global-components.d.ts
|   |-- global.d.ts
|   |-- index.d.ts
|   |-- router.d.ts
|   |-- shims-tsx.d.ts
|   +-- shims-vue.d.ts
|-- .browserslistrc
|-- .dockerignore
|-- .editorconfig
|-- .env
|-- .env.development
|-- .env.production
|-- .env.staging
|-- .gitignore
|-- .lintstagedrc
|-- .markdownlint.json
|-- .npmrc
|-- .nvmrc
|-- .prettierrc.js
|-- .stylelintignore
|-- commitlint.config.js
|-- Dockerfile
|-- eslint.config.js
|-- index.html
|-- LICENSE
|-- package.json
|-- pnpm-lock.yaml
|-- postcss.config.js
|-- pure-admin-thin.code-workspace
|-- README.en-US.md
|-- README.md
|-- stylelint.config.js
|-- tailwind.config.ts
|-- tsconfig.json
|-- vite.config.ts
+-- vite.config.ts.timestamp-1744787977500-55032248df08b.mjs
```
