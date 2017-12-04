VERSION = '1.0'
API_URL = 'https://api.tadata.me/imt/v1/?imdb_id=%s'

TYPE_ORDER = ['trailer', 'behind_the_scenes', 'scene_or_sample']
TYPE_MAP = {
	'trailer': TrailerObject,
	'behind_the_scenes': BehindTheScenesObject,
	'scene_or_sample': SceneOrSampleObject
}

####################################################################################################
def Start():

	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-Agent'] = 'iTunes Movie Trailers/%s (%s %s; Plex Media Server %s)' % (VERSION, Platform.OS, Platform.OSVersion, Platform.ServerVersion)

####################################################################################################
class IMTAgent(Agent.Movies):

	name = 'iTunes Movie Trailers'
	languages = [Locale.Language.NoLanguage]
	primary_provider = False
	contributes_to = [
		'com.plexapp.agents.imdb',
		'com.plexapp.agents.themoviedb'
	]

	def search(self, results, media, lang):

		if media.primary_agent == 'com.plexapp.agents.imdb':

			imdb_id = media.primary_metadata.id

		elif media.primary_agent == 'com.plexapp.agents.themoviedb':

			# Get the IMDb id from the Movie Database Agent
			imdb_id = Core.messaging.call_external_function(
				'com.plexapp.agents.themoviedb',
				'MessageKit:GetImdbId',
				kwargs = dict(
					tmdb_id = media.primary_metadata.id
				)
			)

			if not imdb_id:
				Log("*** Could not find IMDb id for movie with The Movie Database id: %s ***" % (media.primary_metadata.id))
				return None

		results.Append(MetadataSearchResult(
			id = imdb_id,
			score = 100
		))

	def update(self, metadata, media, lang):

		try:
			json_obj = JSON.ObjectFromURL(API_URL % (metadata.id))
		except:
			Log("*** Failed retrieving data from %s ***" % (API_URL % (metadata.id)))
			return None

		if 'error' in json_obj:
			Log("*** An error occurred: %s ***" % (json_obj['error']))
			return None

		extras = []

		for video in json_obj['video']:

			title = video['title']

			# Trailers
			if 'Trailer' in title and Prefs['add_trailers']:
				extra_type = 'trailer'

			# Featurette
			elif 'Featurette' in title and Prefs['add_featurettes']:
				extra_type = 'behind_the_scenes'

			# Clip
			elif 'Clip' in title and Prefs['add_clips']:
				extra_type = 'scene_or_sample'

			else:
				continue

			extras.append({
				'type': extra_type,
				'extra': TYPE_MAP[extra_type](
					url = 'imt://%s/%s' % (metadata.id, String.Quote(title)),
					title = title,
					thumb = video['thumb']
				)
			})

		extras.sort(key=lambda e: TYPE_ORDER.index(e['type']))

		for extra in extras:
			metadata.extras.add(extra['extra'])
