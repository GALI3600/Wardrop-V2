export const metadata = {
  title: "Política de Privacidade | Wardrop",
};

export default function PrivacidadePage() {
  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
      <h1 className="text-3xl font-bold mb-8" style={{ color: "var(--text-primary)" }}>
        Política de Privacidade
      </h1>
      <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
        Última atualização: 4 de março de 2026
      </p>

      <div className="space-y-8" style={{ color: "var(--text-primary)" }}>
        <Section title="1. Introdução">
          <p>
            O Wardrop (&quot;nós&quot;, &quot;nosso&quot;) é um rastreador de preços que ajuda
            consumidores a acompanhar variações de preço em marketplaces brasileiros. Esta
            política descreve como coletamos, usamos e protegemos suas informações.
          </p>
        </Section>

        <Section title="2. Dados que coletamos">
          <ul className="list-disc pl-6 space-y-2">
            <li>
              <strong>Dados de conta:</strong> e-mail e senha (criptografada) quando você cria
              uma conta.
            </li>
            <li>
              <strong>Dados de produtos:</strong> URLs, nomes, preços e imagens dos produtos que
              você rastreia. Esses dados são obtidos de páginas públicas de marketplaces.
            </li>
            <li>
              <strong>Dados de uso:</strong> interações básicas com a extensão e o painel web
              para melhorar o serviço.
            </li>
          </ul>
        </Section>

        <Section title="3. Como usamos seus dados">
          <ul className="list-disc pl-6 space-y-2">
            <li>Monitorar preços dos produtos que você escolheu rastrear.</li>
            <li>Enviar notificações sobre quedas de preço.</li>
            <li>Exibir histórico de preços e comparações entre marketplaces.</li>
            <li>Melhorar e manter o funcionamento do serviço.</li>
          </ul>
        </Section>

        <Section title="4. Armazenamento e segurança">
          <p>
            Seus dados são armazenados em servidores seguros. Senhas são criptografadas com
            hash e nunca armazenadas em texto puro. Utilizamos HTTPS em todas as comunicações
            entre a extensão, o site e nossos servidores.
          </p>
        </Section>

        <Section title="5. Compartilhamento de dados">
          <p>
            Não vendemos, alugamos ou compartilhamos seus dados pessoais com terceiros. Dados
            de produtos (preços, nomes) são obtidos de páginas públicas e podem ser exibidos de
            forma agregada e anônima.
          </p>
        </Section>

        <Section title="6. Armazenamento local (extensão)">
          <p>
            A extensão utiliza o armazenamento local do navegador (chrome.storage) para salvar
            produtos rastreados e preferências. Esses dados permanecem no seu dispositivo e
            podem ser apagados a qualquer momento desinstalando a extensão ou limpando os dados
            do navegador.
          </p>
        </Section>

        <Section title="7. Seus direitos">
          <ul className="list-disc pl-6 space-y-2">
            <li>Acessar seus dados pessoais a qualquer momento pelo painel web.</li>
            <li>Excluir sua conta e todos os dados associados.</li>
            <li>Deixar de rastrear qualquer produto a qualquer momento.</li>
          </ul>
        </Section>

        <Section title="8. Permissões da extensão">
          <ul className="list-disc pl-6 space-y-2">
            <li>
              <strong>storage:</strong> salvar produtos rastreados e preferências localmente.
            </li>
            <li>
              <strong>notifications:</strong> alertar sobre quedas de preço.
            </li>
            <li>
              <strong>activeTab:</strong> ler dados do produto na página que você está visitando.
            </li>
            <li>
              <strong>host_permissions:</strong> comunicar com nosso servidor para processar e
              armazenar dados de produtos.
            </li>
          </ul>
        </Section>

        <Section title="9. Alterações nesta política">
          <p>
            Podemos atualizar esta política periodicamente. Alterações significativas serão
            comunicadas pelo site ou pela extensão.
          </p>
        </Section>

        <Section title="10. Contato">
          <p>
            Em caso de dúvidas sobre esta política, entre em contato pelo e-mail:{" "}
            <a
              href="mailto:contato@wardrop.serverapp.com.br"
              className="underline"
              style={{ color: "var(--accent)" }}
            >
              contato@wardrop.serverapp.com.br
            </a>
          </p>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-xl font-semibold mb-3">{title}</h2>
      <div className="leading-relaxed space-y-3" style={{ color: "var(--text-secondary)" }}>
        {children}
      </div>
    </section>
  );
}
