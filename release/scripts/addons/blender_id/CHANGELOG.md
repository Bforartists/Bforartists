# Blender ID Add-on Changelog

# Version 2.1 (released 2019-08-18)

- Add a timeout to communication with Blender ID. Any attempt at communication will now time out
  after 5 seconds, and be re-tried 5 times. Combined a request can "hang" for a minute, but not
  longer than that.


# Version 2.0 (released 2019-07-09)

- Require Blender 2.80+.
- Use the new URL https://id.blender.org/ for communication with Blender ID.
- API change: `blender_id.get_subclient_user_id()` now returns `''` instead of `None` when the user
  is not logged in.
- Log which Blender ID instance is communicated with.
- Show which Blender ID instance is communicated with in the addon preferences,
  if it was overridden by setting the `BLENDER_ID_ENDPOINT` environment variable.
- Automatically retry failed connections to Blender ID for more stability.
- Include Blender and add-on version in User-Agent header when communicating with Blender ID.


# Version 1.5 (released 2018-07-03)

- Support Blender 2.80.


## Version 1.4.1 (released 2017-12-15)

- Improved error reporting when validating a token fails due to
  connection errors.


## Version 1.4 (released 2017-12-05)

- Added an extra date/time format for parsing the authentication token expiry date.
- Always show the "Validate" button when the user is logged in. This actively checks the token with
  the server, whereas the "You are logged in" only bases that statement on locally-available
  information (there is a token and it hasn't expired yet).


## Version 1.3 (released 2017-06-14)

- Show a message after logging out.
- Store token expiry date in profile JSON.
- Show "validate" button when the token expiration is unknown.
- Urge the user to log out & back in again to refresh the auth token if it expires within 2 weeks.
- Added a method `validate_token()` to the public Blender ID Add-on API.


## Older versions

The history of older versions can be found in the
[Blender ID Add-on Git repository](https://developer.blender.org/diffusion/BIA/).
