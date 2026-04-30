/**
 * Navigate to a screen registered on the root stack (e.g. AlertDetail, DeviceDetail)
 * from nested navigators (drawer/tabs).
 */
export function navigateToRootStack(navigation, screenName, params) {
  let nav = navigation;
  while (nav && typeof nav.getParent === 'function') {
    const parent = nav.getParent();
    if (!parent) break;
    nav = parent;
  }
  if (nav && typeof nav.navigate === 'function') {
    nav.navigate(screenName, params);
  }
}
