+++
title = 'Days'
# Days aren't pages of their own: the About page shows them in a calendar.
[build]
  render = 'never'
  list = 'never'
[cascade.build]
  render = 'never'
  list = 'local'
  publishResources = true
+++
