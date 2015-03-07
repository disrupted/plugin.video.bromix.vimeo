from resources.lib.kodion.items import DirectoryItem, UriItem
from resources.lib.vimeo.client import Client

__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.vimeo import helper


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._local_map.update({'vimeo.my-feed': 30500,
                                'vimeo.watch-later': 30107,
                                'vimeo.likes': 30501,
                                'vimeo.like': 30518,
                                'vimeo.unlike': 30519,
                                'vimeo.following': 30502,
                                'vimeo.watch-later.add': 30516,
                                'vimeo.watch-later.remove': 30517,
                                'vimeo.sign-in': 30111,
                                'vimeo.channels': 30503,
                                'vimeo.groups': 30504})

        self._client = None
        self._is_logged_in = False
        pass

    def get_wizard_supported_views(self):
        return ['default', 'episodes']

    def is_logged_in(self):
        return self._is_logged_in

    def reset_client(self):
        self._client = None
        pass

    def get_client(self, context):
        # set the items per page (later)
        items_per_page = context.get_settings().get_items_per_page()

        access_manager = context.get_access_manager()
        access_token = access_manager.get_access_token()
        if access_manager.is_new_login_credential() or not access_token or access_manager.is_access_token_expired():
            # reset access_token
            access_manager.update_access_token('')
            # we clear the cache, so none cached data of an old account will be displayed.
            context.get_function_cache().clear()
            # reset the client
            self._client = None
            pass

        if not self._client:
            if access_manager.has_login_credentials() or access_manager.has_refresh_token():
                username, password = access_manager.get_login_credentials()
                access_token = access_manager.get_access_token()
                refresh_token = access_manager.get_refresh_token()

                # create a new access_token
                if not access_token and username and password:
                    data = Client().login(username, password)
                    access_manager.update_access_token(access_token=data.get('oauth_token'),
                                                       refresh_token=data.get('oauth_token_secret'))
                    pass

                access_token = access_manager.get_access_token()
                refresh_token = access_manager.get_refresh_token()

                if access_token and refresh_token:
                    self._client = Client(oauth_token=access_token, oauth_token_secret=refresh_token)
                else:
                    self._client = Client()
                    pass

                self._is_logged_in = access_token != ''
            else:
                self._client = Client()
                pass
            pass

        return self._client

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    def on_search(self, search_text, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        result = []

        client = self.get_client(context)
        page = int(context.get_param('page', '1'))
        xml = client.search(query=search_text, page=page)
        result.extend(helper.do_xml_videos_response(context, self, xml))

        return result

    # LIST: VIDEO OF A CHANNEL
    @kodion.RegisterProviderPath('^/channel/(?P<channel_id>\d+)/$')
    def _on_channel(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        channel_id = re_match.group('channel_id')
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_channel_videos(channel_id=channel_id, page=page))

    # LIST: VIDEO OF A GROUP
    @kodion.RegisterProviderPath('^/group/(?P<group_id>\d+)/$')
    def _on_group(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        group_id = re_match.group('group_id')
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_group_videos(group_id=group_id, page=page))

    # LIST: MY FEEDs
    @kodion.RegisterProviderPath('^/user/me/feed/$')
    def _on_me_feed(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_my_feed(page=page))

    # LIST: WATCH LATER
    @kodion.RegisterProviderPath('^/user/me/watch-later/$')
    def _on_me_watch_later(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_watch_later(page=page))

    @kodion.RegisterProviderPath('^/user/(?P<user_id>me|\d+)/$')
    def _on_user(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)

        user_id = re_match.group('user_id')
        page = int(context.get_param('page', '1'))

        result = []
        if page == 1:
            # Likes
            likes_item = DirectoryItem(context.localize(self._local_map['vimeo.likes']),
                                          context.create_uri(['user', user_id, 'likes']),
                                          image=context.create_resource_path('media', 'likes.png'))
            likes_item.set_fanart(self.get_fanart(context))
            result.append(likes_item)

            # Following
            following_item = DirectoryItem(context.localize(self._local_map['vimeo.following']),
                                           context.create_uri(['user', user_id, 'following']),
                                           image=context.create_resource_path('media', 'channels.png'))
            following_item.set_fanart(self.get_fanart(context))
            result.append(following_item)

            # Groups
            groups_item = DirectoryItem(context.localize(self._local_map['vimeo.groups']),
                                           context.create_uri(['user', user_id, 'groups']),
                                           image=context.create_resource_path('media', 'channels.png'))
            groups_item.set_fanart(self.get_fanart(context))
            result.append(groups_item)

            # Channels
            channels_item = DirectoryItem(context.localize(self._local_map['vimeo.channels']),
                                           context.create_uri(['user', user_id, 'channels']),
                                           image=context.create_resource_path('media', 'channels.png'))
            channels_item.set_fanart(self.get_fanart(context))
            result.append(channels_item)
            pass

        client = self.get_client(context)
        result.extend(
            helper.do_xml_videos_response(context, self, client.get_videos_of_user(user_id=user_id, page=page)))
        return result

    # LIST: FOLLOWING
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/following\/$')
    def _on_user_following(self, context, re_match):
        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        if user_id == 'me':
            user_id = None
            pass

        client = self.get_client(context)
        return helper.do_xml_user_response(context, self, client.get_all_contacts(user_id=user_id, page=page))

    # LIST: GROUPS
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/groups\/$')
    def _on_user_groups(self, context, re_match):
        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        if user_id == 'me':
            user_id = None
            pass

        client = self.get_client(context)
        return helper.do_xml_groups_response(context, self, client.get_groups(user_id=user_id, page=page))

    # LIST: CHANNELS
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/channels\/$')
    def _on_user_channels(self, context, re_match):
        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        if user_id == 'me':
            user_id = None
            pass

        client = self.get_client(context)
        return helper.do_xml_channels_response(context, self, client.get_channels(user_id=user_id, page=page))

    # LIST: LIKES
    @kodion.RegisterProviderPath('^/user/(?P<user_id>me|\d+)/likes/$')
    def _on_user_likes(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        if user_id == 'me':
            user_id = None
            pass

        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_video_likes(user_id=user_id, page=page))

    @kodion.RegisterProviderPath('^/play/$')
    def _on_play(self, context, re_match):
        def _compare(item):
            vq = context.get_settings().get_video_quality()
            return vq - item['resolution']

        video_id = context.get_param('video_id')
        client = self.get_client(context)
        video_item = helper.do_xml_video_response(context, self, client.get_video_info(video_id))
        xml = self.get_client(context).get_video_streams(video_id=video_id)

        video_streams = helper.do_xml_to_video_stream(context, self, xml)
        video_stream = kodion.utils.find_best_fit(video_streams, _compare)

        video_item.set_uri(video_stream['url'])
        return video_item

    @kodion.RegisterProviderPath('^/video/(?P<video_id>.+)/like/$')
    def _on_video_like(self, context, re_match):
        video_id = re_match.group('video_id')
        like = context.get_param('like', '0') == '1'

        client = self.get_client(context)
        helper.do_xml_error(context, self, client.like_video(video_id=video_id, like=like))

        context.get_ui().refresh_container()
        return True

    @kodion.RegisterProviderPath('^/video/(?P<video_id>.+)/watch-later/$')
    def _on_video_watch_later(self, context, re_match):
        video_id = re_match.group('video_id')
        later = context.get_param('later', '0') == '1'

        client = self.get_client(context)
        helper.do_xml_error(context, self, client.watch_video_later(video_id=video_id, later=later))

        context.get_ui().refresh_container()
        return True

    @kodion.RegisterProviderPath('^/sign/in/$')
    def _on_sign_in(self, context, re_match):
        context.get_ui().open_settings()
        return True

    def on_root(self, context, re_match):
        result = []

        client = self.get_client(context)

        if self._is_logged_in:
            # my feed
            feed_item = DirectoryItem(context.localize(self._local_map['vimeo.my-feed']),
                                         context.create_uri(['user', 'me', 'feed']),
                                         image=context.create_resource_path('media', 'new_uploads.png'))
            feed_item.set_fanart(self.get_fanart(context))
            result.append(feed_item)

            # Watch Later
            watch_later_item = DirectoryItem(context.localize(self._local_map['vimeo.watch-later']),
                                             context.create_uri(['user', 'me', 'watch-later']),
                                             image=context.create_resource_path('media', 'watch_later.png'))
            watch_later_item.set_fanart(self.get_fanart(context))
            result.append(watch_later_item)

            # my likes
            likes_item= DirectoryItem(context.localize(self._local_map['vimeo.likes']),
                                          context.create_uri(['user', 'me', 'likes']),
                                          image=context.create_resource_path('media', 'likes.png'))
            likes_item.set_fanart(self.get_fanart(context))
            result.append(likes_item)

            # Groups
            groups_item = DirectoryItem(context.localize(self._local_map['vimeo.groups']),
                                           context.create_uri(['user', 'me', 'groups']),
                                           image=context.create_resource_path('media', 'channels.png'))
            groups_item.set_fanart(self.get_fanart(context))
            result.append(groups_item)

            # Following
            following_item = DirectoryItem(context.localize(self._local_map['vimeo.following']),
                                           context.create_uri(['user', 'me', 'following']),
                                           image=context.create_resource_path('media', 'channels.png'))
            following_item.set_fanart(self.get_fanart(context))
            result.append(following_item)
            pass

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        result.append(search_item)

        # sign in
        if not self._is_logged_in:
            sign_in_item = DirectoryItem(context.localize(self._local_map['vimeo.sign-in']),
                                         context.create_uri(['sign', 'in']),
                                         image=context.create_resource_path('media', 'sign_in.png'))
            sign_in_item.set_fanart(self.get_fanart(context))
            result.append(sign_in_item)
            pass

        return result

    def set_content_type(self, context, content_type):
        context.set_content_type(content_type)
        if content_type == kodion.constants.content_type.EPISODES:
            context.add_sort_method(kodion.constants.sort_method.UNSORTED,
                                    kodion.constants.sort_method.VIDEO_RUNTIME,
                                    kodion.constants.sort_method.VIDEO_TITLE,
                                    kodion.constants.sort_method.VIDEO_YEAR)
            pass
        pass

    pass