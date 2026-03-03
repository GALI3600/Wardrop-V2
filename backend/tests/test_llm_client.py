from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm_client import LLMResponse, call_llm


class TestLLMResponse:
    def test_fields(self):
        r = LLMResponse(text="hi", input_tokens=10, output_tokens=5, model="m")
        assert r.text == "hi"
        assert r.input_tokens == 10
        assert r.output_tokens == 5
        assert r.model == "m"

    def test_immutable(self):
        r = LLMResponse(text="hi", input_tokens=10, output_tokens=5, model="m")
        with pytest.raises(AttributeError):
            r.text = "bye"


class TestCallLLMDispatch:
    @pytest.mark.asyncio
    async def test_unknown_provider_raises(self):
        with patch("app.services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "unknown"
            with pytest.raises(ValueError, match="Unknown LLM provider"):
                await call_llm(user_content="test")

    @pytest.mark.asyncio
    async def test_dispatches_to_anthropic(self):
        mock_response = LLMResponse(text="ok", input_tokens=10, output_tokens=5, model="claude-haiku-4-5-20251001")
        with patch("app.services.llm_client.settings") as mock_settings, \
             patch("app.services.llm_client._call_anthropic", new_callable=AsyncMock, return_value=mock_response) as mock_fn:
            mock_settings.llm_provider = "anthropic"
            result = await call_llm(user_content="test", system_prompt="sys")
            mock_fn.assert_called_once_with("test", "sys", 1024)
            assert result.text == "ok"

    @pytest.mark.asyncio
    async def test_dispatches_to_groq(self):
        mock_response = LLMResponse(text="ok", input_tokens=10, output_tokens=5, model="llama-3.3-70b-versatile")
        with patch("app.services.llm_client.settings") as mock_settings, \
             patch("app.services.llm_client._call_groq", new_callable=AsyncMock, return_value=mock_response) as mock_fn:
            mock_settings.llm_provider = "groq"
            result = await call_llm(user_content="hello")
            mock_fn.assert_called_once_with("hello", "", 1024)
            assert result.model == "llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_dispatches_to_openai(self):
        mock_response = LLMResponse(text="ok", input_tokens=10, output_tokens=5, model="gpt-4o-mini")
        with patch("app.services.llm_client.settings") as mock_settings, \
             patch("app.services.llm_client._call_openai", new_callable=AsyncMock, return_value=mock_response) as mock_fn:
            mock_settings.llm_provider = "openai"
            result = await call_llm(user_content="hello")
            mock_fn.assert_called_once()
            assert result.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_dispatches_to_gemini(self):
        mock_response = LLMResponse(text="ok", input_tokens=10, output_tokens=5, model="gemini-2.5-flash")
        with patch("app.services.llm_client.settings") as mock_settings, \
             patch("app.services.llm_client._call_gemini", new_callable=AsyncMock, return_value=mock_response) as mock_fn:
            mock_settings.llm_provider = "gemini"
            result = await call_llm(user_content="hello")
            mock_fn.assert_called_once()
            assert result.model == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_custom_max_tokens(self):
        mock_response = LLMResponse(text="ok", input_tokens=10, output_tokens=5, model="test")
        with patch("app.services.llm_client.settings") as mock_settings, \
             patch("app.services.llm_client._call_groq", new_callable=AsyncMock, return_value=mock_response) as mock_fn:
            mock_settings.llm_provider = "groq"
            await call_llm(user_content="hello", max_tokens=2048)
            mock_fn.assert_called_once_with("hello", "", 2048)


class TestCallAnthropic:
    @pytest.mark.asyncio
    async def test_call_anthropic(self):
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="response text")]
        mock_message.usage.input_tokens = 100
        mock_message.usage.output_tokens = 50

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("app.services.llm_client.anthropic") as mock_anthropic, \
             patch("app.services.llm_client.settings") as mock_settings:
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.anthropic_model = "claude-haiku-4-5-20251001"

            from app.services.llm_client import _call_anthropic
            result = await _call_anthropic("user msg", "system msg", 1024)

        assert result.text == "response text"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.model == "claude-haiku-4-5-20251001"

    @pytest.mark.asyncio
    async def test_anthropic_not_installed(self):
        with patch("app.services.llm_client.anthropic", None):
            from app.services.llm_client import _call_anthropic
            with pytest.raises(ImportError):
                await _call_anthropic("msg", "sys", 1024)


class TestCallOpenAICompatible:
    @pytest.mark.asyncio
    async def test_call_groq(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "groq response"
        mock_response.usage.prompt_tokens = 80
        mock_response.usage.completion_tokens = 40

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        mock_cls = MagicMock(return_value=mock_client)

        with patch("app.services.llm_client.AsyncGroq", mock_cls), \
             patch("app.services.llm_client.settings") as mock_settings:
            mock_settings.groq_api_key = "gsk_test"
            mock_settings.groq_model = "llama-3.3-70b-versatile"

            from app.services.llm_client import _call_groq
            result = await _call_groq("user msg", "system msg", 512)

        assert result.text == "groq response"
        assert result.input_tokens == 80
        assert result.output_tokens == 40
        assert result.model == "llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_groq_not_installed(self):
        with patch("app.services.llm_client.AsyncGroq", None):
            from app.services.llm_client import _call_groq
            with pytest.raises(ImportError):
                await _call_groq("msg", "sys", 1024)
