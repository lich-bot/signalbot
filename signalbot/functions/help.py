"""Help module."""


class Help:
    """Defining base class for inheritence."""

    @staticmethod
    def help():
        """Return all available commands."""
        return """
        cmnds
        ----
        !help
        !version
        !rand
        !flip
        !chuck
        !gif
        !haiku
        !hn
        !twitch
        !bored
        !trivia
        !xkcd
        !tmdb
        """
